#!/usr/bin/env python3
"""Export 12 editable DFD pages using the same layout as the SVG files."""

import html
from pathlib import Path
import xml.etree.ElementTree as ET

from diagram_layout import PALETTE, edge_points, layout, midpoint, node_html
from generate_diagrams import all_diagrams

DRAWIO_PATH = Path(__file__).resolve().parent / "medikamente-dfd.drawio"
PAGE_NAMES = ["Регистрация", "Запись", "Приём и ЭМК", "Лаборатория", "Оплата", "Аналитика"]


def cell(root, identifier, value, style, x, y, width, height):
    element = ET.SubElement(root, "mxCell", {
        "id": identifier, "parent": "1", "vertex": "1",
        "value": value, "style": style})
    ET.SubElement(element, "mxGeometry", {
        "x": str(round(x, 2)), "y": str(round(y, 2)),
        "width": str(round(width, 2)), "height": str(round(height, 2)),
        "as": "geometry"})
    return element


def main():
    file = ET.Element("mxfile", {"host": "app.diagrams.net", "type": "device"})
    for index, (name, diagram) in enumerate(all_diagrams):
        prepared = layout(diagram)
        data = prepared["data"]
        mode = "As-Is" if name.endswith("as-is") else "To-Be"
        page_name = f"P{index // 2 + 1} {PAGE_NAMES[index // 2]} ({mode})"
        page = ET.SubElement(file, "diagram", {"id": name, "name": page_name})
        model = ET.SubElement(page, "mxGraphModel", {
            "grid": "1", "gridSize": "10", "guides": "1", "connect": "1",
            "page": "1", "pageScale": "1", "background": "#ffffff",
            "pageWidth": str(prepared["width"]), "pageHeight": str(prepared["height"])})
        root = ET.SubElement(model, "root")
        ET.SubElement(root, "mxCell", {"id": "0"})
        ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
        heading = "<br>".join(html.escape(s) for s in prepared["title"])
        subtitle = "<br>".join(html.escape(s) for s in prepared["subtitle"])
        header = f'<b style="font-size:22px">{heading}</b><br>{subtitle}<br><br>' \
            'Стрелка: направление передачи данных. Красный: уязвимость. ' \
            'Зелёный: мера защиты. Синий: внешний участник.'
        cell(root, "header", header,
             "text;html=1;align=left;verticalAlign=top;fontSize=14;"
             "fontFamily=DejaVu Sans;fontColor=#0f172a;whiteSpace=wrap;",
             28, 12, prepared["width"] - 56, prepared["graph_top"] - 32)
        by_id = {e["id"]: e for e in diagram["elements"]}
        objects = {e["name"]: e for e in data["objects"] if e.get("name") in by_id}
        bounds = {}
        for identifier, obj in objects.items():
            element = by_id[identifier]
            px, py = map(float, obj["pos"].split(","))
            width, height = float(obj["width"]) * 72, float(obj["height"]) * 72
            x = px - width / 2 + 28
            y = prepared["graph_top"] + prepared["graph_height"] - py - height / 2
            bounds[identifier] = (x, y, width, height)
            color, fill = PALETTE["entity" if element["type"] == "entity"
                                  else element.get("status", "normal")]
            shape = {"entity": "shape=rectangle;rounded=0;",
                     "process": "shape=rectangle;rounded=1;arcSize=10;",
                     "store": "shape=partialRectangle;top=1;bottom=1;left=1;right=0;"}[element["type"]]
            label = node_html(element).replace('POINT-SIZE="', 'style="font-size:')
            label = label.replace('font-size:14"', 'font-size:14px"') \
                .replace('font-size:17"', 'font-size:17px"')
            label = label.replace(' WIDTH="270"', '')
            cell(root, identifier, label,
                 shape + f"whiteSpace=wrap;html=1;fillColor={fill};strokeColor={color};"
                 "strokeWidth=2;fontColor=#0f172a;fontSize=14;fontFamily=DejaVu Sans;"
                 "align=center;verticalAlign=middle;spacing=10;",
                 x, y, width, height)
        for edge in (e for e in data["edges"] if e.get("id")):
            source = data["objects"][edge["tail"]]["name"]
            target = data["objects"][edge["head"]]["name"]
            points = [(p[0] + 28, prepared["graph_top"] + prepared["graph_height"] - p[1])
                      for p in edge_points(edge)]
            fractions = []
            for identifier, point in [(source, points[0]), (target, points[-1])]:
                x, y, w, h = bounds[identifier]
                fractions.append((max(0, min(1, (point[0] - x) / w)),
                                  max(0, min(1, (point[1] - y) / h))))
            style = f"html=1;strokeColor={edge['color']};strokeWidth=1.8;" \
                f"fontColor={edge['fontcolor']};fontSize=14;fontFamily=DejaVu Sans;" \
                "endArrow=block;endFill=1;endSize=9;rounded=0;" \
                "labelBackgroundColor=#ffffff;spacing=5;" \
                f"exitX={fractions[0][0]};exitY={fractions[0][1]};exitPerimeter=0;" \
                f"entryX={fractions[1][0]};entryY={fractions[1][1]};entryPerimeter=0;"
            value = "<br>".join(html.escape(s) for s in edge["label"].splitlines())
            connector = ET.SubElement(root, "mxCell", {
                "id": edge["id"], "parent": "1", "source": source, "target": target,
                "edge": "1", "value": value, "style": style})
            geometry = ET.SubElement(connector, "mxGeometry", {"relative": "1", "as": "geometry"})
            waypoints = ET.SubElement(geometry, "Array", {"as": "points"})
            for x, y in points[1:-1]:
                ET.SubElement(waypoints, "mxPoint", {"x": str(round(x, 2)), "y": str(round(y, 2))})
            middle = midpoint(points)
            lx, ly = map(float, edge["lp"].split(","))
            ET.SubElement(geometry, "mxPoint", {
                "x": str(round(lx + 28 - middle[0], 2)),
                "y": str(round(prepared["graph_top"] + prepared["graph_height"] - ly - middle[1], 2)),
                "as": "offset"})
        if prepared["notes"]:
            content = '<b>' + html.escape(prepared["notes"][0]) + '</b><br>' \
                + "<br>".join(html.escape(s) for s in prepared["notes"][1:])
            cell(root, "security_notes", content,
                 "rounded=1;whiteSpace=wrap;html=1;fillColor=#f0fdf4;"
                 "strokeColor=#166534;fontColor=#14532d;fontSize=14;"
                 "fontFamily=DejaVu Sans;align=left;spacing=12;",
                 20, prepared["graph_top"] + prepared["graph_height"] + 19,
                 prepared["width"] - 40, len(prepared["notes"]) * 21 + 16)
    ET.indent(file)
    DRAWIO_PATH.write_text(ET.tostring(file, encoding="unicode") + "\n", encoding="utf-8")
    print(f"Generated: {DRAWIO_PATH.name}")


if __name__ == "__main__":
    main()
