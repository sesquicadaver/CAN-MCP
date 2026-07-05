# -*- coding: utf-8 -*-
#
# ARCHIVE — vulture runner logic from codimension/analysis/notused.py
# Extracted to codimension_core.analyzer (run_vulture, analyze_dead_code).
# Do not import from Carantine in production code.
#
# Reference date: 2026-07-05

"""Legacy vulture subprocess runner (GUI-specific parts removed)."""

# Original IDE methods mapped to core:
#   _get_exclude_patterns  -> build_vulture_exclude_patterns
#   _get_pyproject_config  -> find_pyproject_vulture_config
#   __run (subprocess)     -> run_vulture / analyze_dead_code
