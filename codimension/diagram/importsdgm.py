# -*- coding: utf-8 -*-
#
# codimension - graphics python two-way code editor and analyzer
# Copyright (C) 2010-2017  Sergey Satskiy <sergey.satskiy@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""imports diagram dialog"""

import logging
import os
import os.path

from cdmpyparser import getBriefModuleInfoFromMemory
from ui.qt import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QLabel,
    QProgressBar,
    Qt,
    QTimer,
    QVBoxLayout,
)
from utils.fileutils import isPythonFile
from utils.globals import GlobalData
from utils.importutils import getRequirementsHint, getUnresolvedPackageNames

from analysis.core_bridge import core_project_from_ide
from codimension_core.import_diagram import (
    DgmConnection,
    DgmDocstring,
    DgmModule,
    ImportDiagramModel,
    ImportDiagramOptions as CoreImportDiagramOptions,
    add_single_file_to_model,
)
from utils.pixmapcache import getPixmap

from .importsdgmgraphics import (
    ImportsDgmBuiltInModule,
    ImportsDgmDependConn,
    ImportsDgmDocConn,
    ImportsDgmDocNote,
    ImportsDgmEdgeLabel,
    ImportsDgmModuleOfInterest,
    ImportsDgmOtherPrjModule,
    ImportsDgmSystemWideModule,
    ImportsDgmUnknownModule,
)
from .plaindotparser import getGraphFromDescriptionData


class ImportDiagramOptions:
    """Holds the generated diagram settings"""

    def __init__(self):
        self.includeClasses = True
        self.includeFuncs = True
        self.includeGlobs = True
        self.includeDocs = False
        self.includeConnText = True

    def to_core(self) -> CoreImportDiagramOptions:
        return CoreImportDiagramOptions.from_legacy(
            include_classes=self.includeClasses,
            include_funcs=self.includeFuncs,
            include_globs=self.includeGlobs,
            include_docs=self.includeDocs,
            include_conn_text=self.includeConnText,
        )


class ImportsDiagramDialog(QDialog):
    """Imports diagram properties dialog implementation"""

    # Options of providing a diagram
    SingleFile = 0
    DirectoryFiles = 1
    ProjectFiles = 2
    SingleBuffer = 3

    def __init__(self, option, path="", parent=None):
        QDialog.__init__(self, parent)

        self.__cancelRequest = False
        self.__inProgress = False
        self.__option = option
        self.__path = path

        # Avoid pylint complains
        self.includeClassesBox = None
        self.includeFuncsBox = None
        self.includeGlobsBox = None
        self.includeDocsBox = None
        self.includeConnTextBox = None

        self.options = ImportDiagramOptions()

        self.__createLayout()
        title = "Imports diagram settings for "
        if self.__option == self.SingleFile:
            title += os.path.basename(self.__path)
        elif self.__option == self.DirectoryFiles:
            title += "directory " + self.__path
        elif self.__option == self.ProjectFiles:
            title += "the whole project"
        else:
            title += "modified file " + os.path.basename(self.__path)
        self.setWindowTitle(title)

    def __updateOptions(self, state=None):
        """Updates the saved options"""
        self.options.includeClasses = self.includeClassesBox.isChecked()
        self.options.includeFuncs = self.includeFuncsBox.isChecked()
        self.options.includeGlobs = self.includeGlobsBox.isChecked()
        self.options.includeDocs = self.includeDocsBox.isChecked()
        self.options.includeConnText = self.includeConnTextBox.isChecked()

    def __createLayout(self):
        """Creates the dialog layout"""
        self.resize(400, 100)
        self.setSizeGripEnabled(True)

        verticalLayout = QVBoxLayout(self)

        # Check boxes
        self.includeClassesBox = QCheckBox(self)
        self.includeClassesBox.setText("Show &classes in modules")
        self.includeClassesBox.setChecked(self.options.includeClasses)
        self.includeClassesBox.stateChanged.connect(self.__updateOptions)
        self.includeFuncsBox = QCheckBox(self)
        self.includeFuncsBox.setText("Show &functions in modules")
        self.includeFuncsBox.setChecked(self.options.includeFuncs)
        self.includeFuncsBox.stateChanged.connect(self.__updateOptions)
        self.includeGlobsBox = QCheckBox(self)
        self.includeGlobsBox.setText("Show &global variables in modules")
        self.includeGlobsBox.setChecked(self.options.includeGlobs)
        self.includeGlobsBox.stateChanged.connect(self.__updateOptions)
        self.includeDocsBox = QCheckBox(self)
        self.includeDocsBox.setText("Show modules &docstrings")
        self.includeDocsBox.setChecked(self.options.includeDocs)
        self.includeDocsBox.stateChanged.connect(self.__updateOptions)
        self.includeConnTextBox = QCheckBox(self)
        self.includeConnTextBox.setText("Show connection &labels")
        self.includeConnTextBox.setChecked(self.options.includeConnText)
        self.includeConnTextBox.stateChanged.connect(self.__updateOptions)

        verticalLayout.addWidget(self.includeClassesBox)
        verticalLayout.addWidget(self.includeFuncsBox)
        verticalLayout.addWidget(self.includeGlobsBox)
        verticalLayout.addWidget(self.includeDocsBox)
        verticalLayout.addWidget(self.includeConnTextBox)

        # Buttons at the bottom
        buttonBox = QDialogButtonBox(self)
        buttonBox.setOrientation(Qt.Horizontal)
        buttonBox.setStandardButtons(QDialogButtonBox.Cancel)
        generateButton = buttonBox.addButton("Generate", QDialogButtonBox.ActionRole)
        generateButton.setDefault(True)
        generateButton.clicked.connect(self.accept)
        verticalLayout.addWidget(buttonBox)

        buttonBox.rejected.connect(self.close)


class ImportsDiagramProgress(QDialog):
    """Progress of the diagram generator"""

    def __init__(self, what, options, path="", buf="", parent=None):
        QDialog.__init__(self, parent)
        self.__cancelRequest = False
        self.__inProgress = False

        self.__what = what
        self.__options = options
        self.__path = path  # could be a dir or a file
        self.__buf = buf  # content in case of a modified file

        # Working process data
        self.__participantFiles = []  # Collected list of files
        self.__projectImportDirs = []
        self.__projectImportsCache = {}  # utils.settings -> /full/path/to.py
        self.__dirsToImportsCache = {}  # /dir/path -> { my.mod: path.py, ... }

        self.dataModel = ImportDiagramModel()
        self.scene = QGraphicsScene()

        # Avoid pylint complains
        self.progressBar = None
        self.infoLabel = None

        self.__createLayout()
        self.setWindowTitle("Imports/dependencies diagram generator")
        QTimer.singleShot(0, self.__process)

    def keyPressEvent(self, event):
        """Processes the ESC key specifically"""
        if event.key() == Qt.Key_Escape:
            self.__onClose()
        else:
            QDialog.keyPressEvent(self, event)

    def __createLayout(self):
        """Creates the dialog layout"""
        self.resize(450, 20)
        self.setSizeGripEnabled(True)

        verticalLayout = QVBoxLayout(self)

        # Info label
        self.infoLabel = QLabel(self)
        verticalLayout.addWidget(self.infoLabel)

        # Progress bar
        self.progressBar = QProgressBar(self)
        self.progressBar.setValue(0)
        self.progressBar.setOrientation(Qt.Horizontal)
        verticalLayout.addWidget(self.progressBar)

        # Buttons
        buttonBox = QDialogButtonBox(self)
        buttonBox.setOrientation(Qt.Horizontal)
        buttonBox.setStandardButtons(QDialogButtonBox.Close)
        verticalLayout.addWidget(buttonBox)

        buttonBox.rejected.connect(self.__onClose)

    def __onClose(self):
        """triggered when the close button is clicked"""
        self.__cancelRequest = True
        if not self.__inProgress:
            self.close()

    def __buildParticipants(self):
        """Builds a list of participating files and dirs"""
        if self.__what in [ImportsDiagramDialog.SingleBuffer, ImportsDiagramDialog.SingleFile]:
            # File exists but could be modified
            self.__path = os.path.realpath(self.__path)
            self.__participantFiles.append(self.__path)
            return

        if self.__what == ImportsDiagramDialog.ProjectFiles:
            self.__scanProjectDirs()
            return

        # This is a recursive directory
        self.__path = os.path.realpath(self.__path)
        self.__scanDirForPythonFiles(self.__path + os.path.sep)

    def __scanDirForPythonFiles(self, path):
        """Scans the directory for the python files recursively"""
        for item in os.listdir(path):
            if item in [".svn", ".cvs", ".git", ".hg"]:
                continue
            if os.path.isdir(path + item):
                self.__scanDirForPythonFiles(path + item + os.path.sep)
                continue
            if isPythonFile(path + item):
                self.__participantFiles.append(os.path.realpath(path + item))

    def __scanProjectDirs(self):
        """Populates participant lists from the project files"""
        for fName in GlobalData().project.filesList:
            if isPythonFile(fName):
                self.__participantFiles.append(fName)

    def __addSingleFileToDataModel(self, info, fName):
        """Adds a single file to the data model."""
        project = core_project_from_ide()
        if project is None:
            raise Exception("Project must be loaded for import diagram analysis")
        add_single_file_to_model(
            project,
            self.dataModel,
            info,
            fName,
            self.__options.to_core(),
            self.__allImportErrors,
        )

    def __process(self):
        """Accumulation process"""
        # Intermediate working data
        self.__participantFiles = []
        self.__projectImportDirs = []
        self.__projectImportsCache = {}
        self.__allImportErrors = []

        self.dataModel.clear()
        self.__inProgress = True

        try:
            self.infoLabel.setText("Building the list of files to analyze...")
            QApplication.processEvents()

            # Build the list of participating python files
            self.__buildParticipants()
            self.__projectImportDirs = GlobalData().project.getImportDirsAsAbsolutePaths()

            QApplication.processEvents()
            if self.__cancelRequest:
                QApplication.restoreOverrideCursor()
                self.close()
                return

            self.progressBar.setRange(0, len(self.__participantFiles))
            index = 1

            # Now, parse the files and build the diagram data model
            if self.__what == ImportsDiagramDialog.SingleBuffer:
                info = getBriefModuleInfoFromMemory(str(self.__buf))
                self.__addSingleFileToDataModel(info, self.__path)
            else:
                infoSrc = GlobalData().briefModinfoCache
                for fName in self.__participantFiles:
                    self.progressBar.setValue(index)
                    self.infoLabel.setText("Analyzing " + fName + "...")
                    QApplication.processEvents()
                    if self.__cancelRequest:
                        QApplication.restoreOverrideCursor()
                        self.dataModel.clear()
                        self.close()
                        return
                    info = infoSrc.get(fName)
                    self.__addSingleFileToDataModel(info, fName)
                    index += 1

            # The import caches and other working data are not needed anymore
            self.__participantFiles = None
            self.__projectImportDirs = None
            self.__projectImportsCache = None

            # Generating the graphviz layout
            self.infoLabel.setText("Generating layout using graphviz...")
            QApplication.processEvents()

            graph = getGraphFromDescriptionData(self.dataModel.toGraphviz())
            graph.normalize(self.physicalDpiX(), self.physicalDpiY())
            QApplication.processEvents()
            if self.__cancelRequest:
                QApplication.restoreOverrideCursor()
                self.dataModel.clear()
                self.close()
                return

            # Generate graphics scene
            self.infoLabel.setText("Generating graphics scene...")
            QApplication.processEvents()
            self.__buildGraphicsScene(graph)

            # Clear the data model
            self.dataModel = None
        except Exception as exc:
            QApplication.restoreOverrideCursor()
            logging.error(str(exc))
            self.__inProgress = False
            self.__onClose()
            return

        QApplication.restoreOverrideCursor()
        self.infoLabel.setText("Done")
        QApplication.processEvents()
        self.__inProgress = False

        if self.__allImportErrors:
            unresolved = getUnresolvedPackageNames(self.__allImportErrors)
            hint = getRequirementsHint(
                GlobalData().project.getProjectDir() if GlobalData().project.isLoaded() else None,
                unresolved,
            )
            if hint:
                logging.warning(hint)
            else:
                logging.warning(
                    "Could not resolve %d import(s). This is often caused by relative imports "
                    "or project path settings, not missing pip packages.",
                    len(self.__allImportErrors),
                )
                for err in self.__allImportErrors[:10]:
                    logging.warning(err)
                if len(self.__allImportErrors) > 10:
                    logging.warning("... and %d more", len(self.__allImportErrors) - 10)

        self.accept()

    def __buildGraphicsScene(self, graph):
        """Builds the QT graphics scene"""
        self.scene.clear()
        self.scene.setSceneRect(0, 0, graph.width, graph.height)

        for edge in graph.edges:
            # self.scene.addItem( GraphicsEdge( edge, self ) )
            dataModelObj = self.dataModel.findConnection(edge.tail, edge.head)
            if dataModelObj is None:
                raise Exception("Cannot find the following connection: " + edge.tail + " -> " + edge.head)

            if dataModelObj.kind == DgmConnection.ModuleDoc:
                modObj = self.dataModel.findModule(dataModelObj.source)
                if modObj is None:
                    raise Exception("Cannot find module object: " + dataModelObj.source)
                self.scene.addItem(ImportsDgmDocConn(edge, modObj))
                continue
            if dataModelObj.kind == DgmConnection.ModuleDependency:
                # Find the source module object first
                modObj = self.dataModel.findModule(dataModelObj.source)
                if modObj is None:
                    raise Exception("Cannot find module object: " + dataModelObj.source)
                self.scene.addItem(ImportsDgmDependConn(edge, modObj, dataModelObj))

                if edge.label != "":
                    self.scene.addItem(ImportsDgmEdgeLabel(edge, modObj))
                continue

            raise Exception("Unexpected type of connection: " + str(dataModelObj.kind))

        for node in graph.nodes:
            dataModelObj = self.dataModel.findModule(node.name)
            if dataModelObj is None:
                dataModelObj = self.dataModel.findDocstring(node.name)
            if dataModelObj is None:
                raise Exception("Cannot find object " + node.name)

            if isinstance(dataModelObj, DgmDocstring):
                self.scene.addItem(ImportsDgmDocNote(node, dataModelObj.refFile, dataModelObj.docstring))
                continue

            # OK, this is a module rectangle. Switch by type of the module.
            if dataModelObj.kind == DgmModule.ModuleOfInterest:
                self.scene.addItem(
                    ImportsDgmModuleOfInterest(node, dataModelObj.refFile, dataModelObj, self.physicalDpiX())
                )
            elif dataModelObj.kind == DgmModule.OtherProjectModule:
                self.scene.addItem(
                    ImportsDgmOtherPrjModule(node, dataModelObj.refFile, dataModelObj, self.physicalDpiX())
                )
            elif dataModelObj.kind == DgmModule.SystemWideModule:
                self.scene.addItem(ImportsDgmSystemWideModule(node, dataModelObj.refFile, dataModelObj.docstring))
            elif dataModelObj.kind == DgmModule.BuiltInModule:
                self.scene.addItem(ImportsDgmBuiltInModule(node))
            elif dataModelObj.kind == DgmModule.UnknownModule:
                self.scene.addItem(ImportsDgmUnknownModule(node))
            else:
                raise Exception("Unexpected type of module: " + str(dataModelObj.kind))

            tooltip = dataModelObj.getTooltip()
            if tooltip:
                pixmap = getPixmap("diagramdoc.png")
                docItem = QGraphicsPixmapItem(pixmap)
                docItem.setToolTip(tooltip)
                posX = node.posX + node.width / 2.0 - pixmap.width() / 2.0
                posY = node.posY - node.height / 2.0 - pixmap.height() / 2.0
                docItem.setPos(posX, posY)
                self.scene.addItem(docItem)
