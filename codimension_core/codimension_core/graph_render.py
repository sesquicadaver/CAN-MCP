# -*- coding: utf-8 -*-
"""Render Graph IR to Mermaid and self-contained HTML/SVG for WebView hosts."""

from __future__ import annotations

import html
import json
import math

from .graph_ir import GraphIR


def _safe_mermaid_id(index: int) -> str:
    return f"n{index}"


def graph_to_mermaid(graph: GraphIR) -> str:
    """Convert Graph IR to a Mermaid flowchart string."""
    id_map: dict[str, str] = {}
    lines = ["flowchart LR"]
    for index, node in enumerate(graph.nodes):
        node_id = _safe_mermaid_id(index)
        id_map[node.id] = node_id
        label = html.escape(node.name or node.id, quote=True).replace('"', "'")
        lines.append(f'  {node_id}["{label}"]')

    for edge in graph.edges:
        from_id = id_map.get(edge.from_id, edge.from_id.replace(":", "_").replace(".", "_"))
        to_id = id_map.get(edge.to_id, edge.to_id.replace(":", "_").replace(".", "_"))
        arrow = "-->"
        if edge.label:
            label = html.escape(edge.label, quote=True).replace('"', "'")
            lines.append(f"  {from_id} {arrow}|{label}| {to_id}")
        else:
            lines.append(f"  {from_id} {arrow} {to_id}")
    return "\n".join(lines)


def _layout_nodes(graph: GraphIR) -> dict[str, tuple[float, float]]:
    count = max(len(graph.nodes), 1)
    radius = 220.0 + min(count, 40) * 4.0
    center_x, center_y = 480.0, 360.0
    positions: dict[str, tuple[float, float]] = {}
    for index, node in enumerate(graph.nodes):
        angle = (2.0 * math.pi * index) / count
        positions[node.id] = (
            center_x + radius * math.cos(angle),
            center_y + radius * math.sin(angle),
        )
    return positions


def graph_to_svg(graph: GraphIR, *, width: int = 960, height: int = 720) -> str:
    """Render Graph IR as inline SVG (offline-safe for WebView)."""
    positions = _layout_nodes(graph)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        "<defs><marker id='arrow' markerWidth='8' markerHeight='8' refX='6' refY='3' "
        "orient='auto'><path d='M0,0 L6,3 L0,6 Z' fill='#64748b'/></marker></defs>",
    ]
    for edge in graph.edges:
        start = positions.get(edge.from_id)
        end = positions.get(edge.to_id)
        if start is None or end is None:
            continue
        x1, y1 = start
        x2, y2 = end
        title = html.escape(edge.label or edge.type)
        parts.append(
            f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' "
            f"stroke='#94a3b8' stroke-width='1.5' marker-end='url(#arrow)'>"
            f"<title>{title}</title></line>"
        )
    for node in graph.nodes:
        x, y = positions.get(node.id, (480.0, 360.0))
        label = html.escape(node.name or node.id)
        node_type = html.escape(node.type)
        parts.append(
            f"<g transform='translate({x - 70:.1f},{y - 22:.1f})'>"
            f"<rect width='140' height='44' rx='8' fill='#1e293b' stroke='#38bdf8'/>"
            f"<text x='70' y='18' text-anchor='middle' fill='#e2e8f0' "
            f"font-family='sans-serif' font-size='11'>{label[:24]}</text>"
            f"<text x='70' y='34' text-anchor='middle' fill='#94a3b8' "
            f"font-family='sans-serif' font-size='9'>{node_type}</text>"
            f"</g>"
        )
    parts.append("</svg>")
    return "".join(parts)


def graph_to_html(graph: GraphIR, title: str) -> str:
    """Build a self-contained HTML page with embedded SVG for Cursor WebView."""
    meta = graph.meta or {}
    subtitle = html.escape(str(meta.get("kind", "graph")))
    safe_title = html.escape(title)
    svg = graph_to_svg(graph)
    meta_json = html.escape(json.dumps(meta, indent=2, sort_keys=True))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>{safe_title}</title>
  <style>
    body {{ margin: 0; font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; }}
    header {{ padding: 12px 20px; border-bottom: 1px solid #334155; }}
    h1 {{ margin: 0; font-size: 1.1rem; }}
    .meta {{ color: #94a3b8; font-size: 0.85rem; margin-top: 4px; }}
    main {{ overflow: auto; }}
    pre {{ margin: 0; padding: 12px 20px; font-size: 0.75rem; color: #cbd5e1; }}
  </style>
</head>
<body>
  <header>
    <h1>{safe_title}</h1>
    <div class="meta">{subtitle} · nodes={len(graph.nodes)} · edges={len(graph.edges)}</div>
  </header>
  <main>{svg}</main>
  <pre>{meta_json}</pre>
</body>
</html>
"""
