# -*- coding: utf-8 -*-
#
# codimension - graphics python two-way code editor and analyzer
# Copyright (C) 2010-2016  Sergey Satskiy <sergey.satskiy@gmail.com>
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

"""codimension brief module info cache — thin wrapper over codimension_core.cache."""

from codimension_core.cache import ModuleInfoCache


class BriefModuleInfoCache:
    """Provides the module info cache for the IDE GlobalData layer."""

    def __init__(self) -> None:
        self._cache = ModuleInfoCache()

    def get(self, path: str):
        """Provides the required modinfo."""
        try:
            return self._cache.get(path)
        except FileNotFoundError as exc:
            # Legacy IDE callers expect generic Exception messages.
            raise Exception(str(exc)) from None

    def remove(self, path: str) -> None:
        """Removes one file from the map."""
        self._cache.remove(path)

    def clear(self) -> None:
        """Clears the cache."""
        self._cache.clear()
