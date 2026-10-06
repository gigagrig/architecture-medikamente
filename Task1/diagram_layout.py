"""Shared, content-sized layout for the SVG and editable draw.io exports."""

import html
import json
import math
import subprocess
import textwrap
import xml.etree.ElementTree as ET

FONT = "DejaVu Sans"
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
PALETTE = {
    "normal": ("#475569", "#f8fafc"),
    "vulnerable": ("#b91c1c", "#fff1f2"),
    "secure": ("#166534", "#f0fdf4"),
    "entity": ("#0369a1", "#f0f9ff"),
}


def lines(text, width):
    """Preserve explicit line breaks and wrap long filenames when necessary."""
    return [part for line in text.splitlines() for part in
            textwrap.wrap(line, width=width, break_long_words=True,
                          break_on_hyphens=False)]


def br(text, width):
    return "<BR/>".join(html.escape(line) for line in lines(text, width))


def node_html(element):
    kind = element["type"]
    identifier = element["id"]
    heading = {"entity": "Внешняя сущность", "process": "Процесс",
               "store": "Хранилище"}[kind] + " " + identifier
    rows = [f'<TR><TD><FONT POINT-SIZE="14">{heading}</FONT></TD></TR>',
            f'<TR><TD WIDTH="270"><FONT POINT-SIZE="17"><B>'
            f'{br(element["title"], 29)}</B></FONT></TD></TR>']
    if element.get("subtitle"):
        rows.append(f'<TR><TD><FONT POINT-SIZE="14">'
                    f'{br(element["subtitle"], 34)}</FONT></TD></TR>')
    if element.get("badge"):
        rows.append(f'<TR><TD><FONT POINT-SIZE="14"><B>'
                    f'{br(element["badge"], 30)}</B></FONT></TD></TR>')
    return ('<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" '
            'CELLPADDING="4">' + "".join(rows) + "</TABLE>")


def dot_source(diagram, orientation="LR"):
    nodes = [e for e in diagram["elements"] if e["type"] != "security_badge"]
    result = ['digraph DFD {',
              f'graph [rankdir={orientation}, nodesep=0.9, ranksep=1.15, '
              'bgcolor="white", splines=spline, pad=0.12];',
              f'node [fontname="{FONT}", fontcolor="#0f172a", '
              'penwidth=2, margin="0.16,0.12"];',
              f'edge [fontname="{FONT}", fontsize=14, penwidth=1.8, '
              'arrowsize=0.85, constraint=false];']
    for e in nodes:
        column = {"entity": 0, "process": 1, "store": 2}[e["type"]]
        color, fill = PALETTE["entity" if e["type"] == "entity"
                              else e.get("status", "normal")]
        shape = 'shape=box, style="rounded,filled"' if e["type"] == "process" \
            else 'shape=box, style="filled"'
        label = node_html(e)
        if e["type"] == "store":
            # An open right edge distinguishes a DFD data store from a process.
            shape = 'shape=plain'
            label = (f'<TABLE BORDER="2" SIDES="LTB" CELLBORDER="0" '
                     f'CELLSPACING="0" CELLPADDING="10" COLOR="{color}" '
                     f'BGCOLOR="{fill}"><TR><TD>{label}</TD></TR></TABLE>')
        result.append(f'{json.dumps(e["id"])} [label=<{label}>, {shape}, '
                      f'color="{color}", fillcolor="{fill}", group="col{column}"];')
    groups = [[e["id"] for e in nodes if e["type"] == kind]
              for kind in ("entity", "process", "store")]
    connections = {(f["source"], f["target"]) for f in diagram["flows"]}
    if orientation == "LR":
        for group in groups:
            result.append("{ rank=same; " + ";".join(map(json.dumps, group)) + "; }")
        result.append(" -> ".join(json.dumps(group[0]) for group in groups if group)
                      + ' [style=invis, constraint=true, weight=100];')
    else:
        for index in range(max(map(len, groups))):
            row = []
            for column, group in enumerate(groups):
                if index < len(group):
                    row.append(group[index])
                else:
                    blank = f"blank_{column}_{index}"
                    row.append(blank)
                    result.append(f'{blank} [shape=point, label="", width=0, '
                                  f'style=invis, group="col{column}"];')
            result.append("{ rank=same; " + ";".join(map(json.dumps, row)) + "; }")
            for source, target in zip(row, row[1:]):
                if (source, target) not in connections and (target, source) not in connections:
                    result.append(f'{json.dumps(source)} -> {json.dumps(target)} '
                                  '[style=invis, weight=100];')
        for source, target in zip(groups[1], groups[1][1:]):
            if (source, target) not in connections:
                result.append(f'{json.dumps(source)} -> {json.dumps(target)} '
                              '[style=invis, constraint=true, weight=100];')
    for index, flow in enumerate(diagram["flows"]):
        color = PALETTE[flow.get("style", "normal")][0]
        label = "\n".join(lines(flow["label"], 28))
        sequential = flow["source"] in groups[1] and flow["target"] in groups[1]
        weight = 100 if sequential else 1
        constraint = "true" if sequential and orientation == "TB" else "false"
        result.append(f'{json.dumps(flow["source"])} -> '
                      f'{json.dumps(flow["target"])} '
                      f'[id="flow_{index}", weight={weight}, constraint={constraint}, '
                      f'label={json.dumps(label, ensure_ascii=False)}, '
                      f'color="{color}", fontcolor="{color}"];')
    result.append("}")
    return "\n".join(result)


def note_lines(diagram, width):
    result = []
    for e in diagram["elements"]:
        if e["type"] != "security_badge":
            continue
        result.append(e["title"])
        paragraphs = []
        for line in e.get("subtitle", "").splitlines():
            if line.startswith("•") or not paragraphs:
                paragraphs.append(line)
            else:
                paragraphs[-1] += " " + line.strip()
        for paragraph in paragraphs:
            result.extend(lines(paragraph, max(40, int((width - 64) / 8))))
    return result


def layout(diagram):
    candidates = []
    processes = [e["id"] for e in diagram["elements"] if e["type"] == "process"]
    for orientation in ("LR", "TB"):
        source = dot_source(diagram, orientation).encode("utf-8")
        data = json.loads(subprocess.run(["dot", "-Tjson"], input=source,
                                        capture_output=True, check=True).stdout)
        width = float(data["bb"].split(",")[2])
        positions = {n["name"]: float(n["pos"].split(",")[1])
                     for n in data["objects"] if n.get("name") in processes}
        reversals = sum(positions[a] <= positions[b] for a, b in zip(processes, processes[1:]))
        candidates.append((width + reversals * 1000, source, data))
    # Prefer compact diagrams with processes in reading order from top to bottom.
    _, source, data = min(candidates, key=lambda candidate: candidate[0])
    svg = ET.fromstring(subprocess.run(["dot", "-Tsvg"], input=source,
                                      capture_output=True, check=True).stdout)
    graph_width, graph_height = map(float, data["bb"].split(",")[2:])
    width = math.ceil(graph_width + 56)
    title = lines(diagram["title"], max(55, int((width - 64) / 12)))
    subtitle = lines(diagram["subtitle"], max(65, int((width - 64) / 8)))
    header_height = 30 + len(title) * 28 + len(subtitle) * 21 + 44
    notes = note_lines(diagram, width)
    footer_height = 30 + len(notes) * 21 if notes else 0
    graph_top = header_height + 20
    height = math.ceil(graph_top + graph_height + 32 + footer_height)
    return dict(data=data, svg=svg, width=width, height=height,
                graph_width=graph_width, graph_height=graph_height,
                graph_top=graph_top, title=title, subtitle=subtitle, notes=notes)


def text(parent, x, y, value, size=14, bold=False, color="#334155"):
    element = ET.SubElement(parent, f"{{{SVG_NS}}}text", {
        "x": str(x), "y": str(y), "font-family": FONT,
        "font-size": str(size), "fill": color,
        "font-weight": "700" if bold else "400"})
    element.text = value


def label_bounds(edge):
    records = [d for d in edge.get("_ldraw_", []) if d["op"] == "T"]
    left = min(r["pt"][0] - r["width"] / 2 for r in records) - 6
    right = max(r["pt"][0] + r["width"] / 2 for r in records) + 6
    bottom = min(r["pt"][1] for r in records) - 5
    top = max(r["pt"][1] for r in records) + 16
    return left, bottom, right, top


def render_svg(diagram):
    prepared = layout(diagram)
    width, height = prepared["width"], prepared["height"]
    root = ET.Element(f"{{{SVG_NS}}}svg", {
        "width": str(width), "height": str(height),
        "viewBox": f"0 0 {width} {height}", "role": "img",
        "aria-labelledby": "title description"})
    ET.SubElement(root, f"{{{SVG_NS}}}title", {"id": "title"}).text = diagram["title"]
    ET.SubElement(root, f"{{{SVG_NS}}}desc", {"id": "description"}).text = diagram["subtitle"]
    ET.SubElement(root, f"{{{SVG_NS}}}rect", {
        "width": str(width), "height": str(height), "fill": "white"})
    y = 32
    for line in prepared["title"]:
        text(root, 28, y, line, size=22, bold=True, color="#0f172a")
        y += 28
    for line in prepared["subtitle"]:
        text(root, 28, y, line)
        y += 21
    text(root, 28, y + 8, "Стрелка: направление передачи данных. "
         "Красный: уязвимость. Зелёный: мера защиты. Синий: внешний участник.")
    graph = prepared["svg"].find(f"{{{SVG_NS}}}g")
    graph.set("transform", f'translate(28,{prepared["graph_top"] + prepared["graph_height"]})')
    # Give every flow label an opaque background so an arrow cannot cross its text.
    for edge in (e for e in prepared["data"]["edges"] if e.get("id")):
        group = graph.find(f".//{{{SVG_NS}}}g[@id='{edge['id']}']")
        left, bottom, right, top = label_bounds(edge)
        background = ET.Element(f"{{{SVG_NS}}}rect", {
            "x": str(left), "y": str(-top), "width": str(right - left),
            "height": str(top - bottom), "rx": "4", "fill": "white"})
        position = next(i for i, child in enumerate(group)
                        if child.tag == f"{{{SVG_NS}}}text")
        group.insert(position, background)
    root.append(graph)
    if prepared["notes"]:
        y = prepared["graph_top"] + prepared["graph_height"] + 40
        ET.SubElement(root, f"{{{SVG_NS}}}rect", {
            "x": "20", "y": str(y - 21), "width": str(width - 40),
            "height": str(len(prepared["notes"]) * 21 + 16),
            "rx": "8", "fill": "#f0fdf4", "stroke": "#166534"})
        for index, line in enumerate(prepared["notes"]):
            text(root, 32, y, line, bold=index == 0, color="#14532d")
            y += 21
    ET.indent(root)
    return ET.tostring(root, encoding="unicode") + "\n"


def edge_points(edge):
    """Approximate Graphviz cubic curves with waypoints for draw.io."""
    curve = next(d["points"] for d in edge["_draw_"] if d["op"] == "b")
    points = [curve[0]]
    for index in range(0, len(curve) - 1, 3):
        a, b, c, d = curve[index:index + 4]
        for step in range(1, 9):
            t = step / 8
            points.append([(1-t)**3*a[k] + 3*(1-t)**2*t*b[k]
                           + 3*(1-t)*t*t*c[k] + t**3*d[k] for k in (0, 1)])
    endpoint = edge["pos"].split()[0]
    if endpoint.startswith("e,"):
        points.append(list(map(float, endpoint[2:].split(","))))
    return points


def midpoint(points):
    lengths = [math.dist(a, b) for a, b in zip(points, points[1:])]
    remaining = sum(lengths) / 2
    for a, b, length in zip(points, points[1:], lengths):
        if remaining <= length:
            t = remaining / length if length else 0
            return [a[k] + t * (b[k] - a[k]) for k in (0, 1)]
        remaining -= length
    return points[-1]
