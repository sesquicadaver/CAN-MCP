# -*- coding: utf-8 -*-
"""Legacy symbol id aliases and canonical resolution."""

from __future__ import annotations

from .errors import AmbiguousSymbolIdError, SymbolNotFoundError
from .project import Project
from .symbols import get_symbols, legacy_symbol_id, parse_symbol_query


def build_legacy_alias_map(project: Project) -> dict[str, str]:
    """Map unambiguous legacy basename ids to canonical project-relative ids."""
    buckets: dict[str, list[str]] = {}
    graph = get_symbols(project)
    for node in graph.nodes:
        if node.type not in ("function", "class", "global", "module"):
            continue
        legacy = legacy_symbol_id(node.file, node.type, node.name)
        buckets.setdefault(legacy, []).append(node.id)
    return {legacy: ids[0] for legacy, ids in buckets.items() if len(ids) == 1}


def resolve_symbol_reference(project: Project, reference: str) -> str:
    """Resolve a legacy or canonical symbol reference to a canonical symbol id."""
    project.require_open()
    canonical_ids = {node.id for node in get_symbols(project).nodes}
    if reference in canonical_ids:
        return reference

    alias_map = build_legacy_alias_map(project)
    if reference in alias_map:
        return alias_map[reference]

    file_hint, name = parse_symbol_query(reference)
    if file_hint is None and ":" not in reference:
        candidates = [
            node.id
            for node in get_symbols(project).nodes
            if node.type == "function" and node.name == reference
        ]
        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) > 1:
            raise AmbiguousSymbolIdError(f"Ambiguous symbol reference: {reference}")

    if file_hint and ":" in reference:
        matches = [
            node.id
            for node in get_symbols(project).nodes
            if node.name == name and (node.file.endswith("/" + file_hint) or node.file.endswith("\\" + file_hint))
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise AmbiguousSymbolIdError(f"Ambiguous symbol reference: {reference}")

    if reference in alias_map:
        return alias_map[reference]

    legacy_matches = [legacy for legacy, canonical in alias_map.items() if canonical.endswith(f":{reference}")]
    if len(legacy_matches) == 1:
        return alias_map[legacy_matches[0]]

    raise SymbolNotFoundError(f"Symbol reference not found: {reference}")
