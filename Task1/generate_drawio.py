#!/usr/bin/env python3
"""
Generates Task1/medikamente-dfd.drawio containing 12 diagrams across separate tabs.
Ensures full XML well-formedness.
"""

import os
import html
from generate_diagrams import all_diagrams

DRAWIO_PATH = os.path.join(os.path.dirname(__file__), "medikamente-dfd.drawio")

def xml_attr_escape(s):
    # First convert newlines to <br> if needed
    s = s.replace('\n', '<br>')
    # Then escape for XML attribute
    return html.escape(s, quote=True)

def generate_drawio():
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<mxfile host="app.diagrams.net" version="24.7.5">'
    ]

    for diag_id, (diag_name, diag) in enumerate(all_diagrams, start=1):
        clean_name = diag['title'].split(':')[0].replace('DFD ', '')
        is_as_is = 'as-is' in diag_name.lower()
        mode_str = 'As-Is' if is_as_is else 'To-Be'
        # Extract process short label
        if 'Процесс 1' in clean_name:
            tab_name = f"P1 Регистрация ({mode_str})"
        elif 'Процесс 2' in clean_name:
            tab_name = f"P2 Запись ({mode_str})"
        elif 'Процесс 3' in clean_name:
            tab_name = f"P3 Прием и ЭМК ({mode_str})"
        elif 'Процесс 4' in clean_name:
            tab_name = f"P4 Лаборатория ({mode_str})"
        elif 'Процесс 5' in clean_name:
            tab_name = f"P5 Оплата ({mode_str})"
        elif 'Процесс 6' in clean_name:
            tab_name = f"P6 Аналитика ({mode_str})"
        else:
            tab_name = f"{clean_name} ({mode_str})"
        
        xml_lines.append(f'  <diagram id="diag_{diag_id}" name="{html.escape(tab_name, quote=True)}">')
        xml_lines.append('    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">')
        xml_lines.append('      <root>')
        xml_lines.append('        <mxCell id="0" />')
        xml_lines.append('        <mxCell id="1" parent="0" />')
        
        # Header banner
        header_html = f"<b>{diag['title']}</b><br><font style='font-size: 11px; color: #64748b;'>{diag['subtitle']}</font>"
        header_val = xml_attr_escape(header_html)
        diag_w = diag['width'] - 40
        xml_lines.append(f'        <mxCell id="header_{diag_id}" value="{header_val}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#cbd5e1;align=left;spacingLeft=15;fontSize=13;fontColor=#0f172a;" vertex="1" parent="1">')
        xml_lines.append(f'          <mxGeometry x="20" y="20" width="{diag_w}" height="50" as="geometry" />')
        xml_lines.append('        </mxCell>')
        
        cell_id = 10

        for el in diag['elements']:
            cid = f"cell_{diag_id}_{cell_id}"
            cell_id += 1
            
            x, y, w, h = el['x'], el['y'], el['w'], el['h']
            title = el['title']
            sub = el.get('subtitle', '')
            t = el.get('type')
            badge = el.get('badge', '')
            
            if t == 'entity':
                inner = f"<b>[ВНЕШНЯЯ СУЩНОСТЬ]</b><br><b style='font-size: 13px;'>{title}</b><br><font style='font-size: 10px; color: #475569;'>{sub}</font>"
                style = "shape=rectangle;rounded=0;whiteSpace=wrap;html=1;fillColor=#e0f2fe;strokeColor=#0284c7;strokeWidth=2;fontColor=#0f172a;align=center;"
            elif t == 'process':
                is_vuln = el.get('status') == 'vulnerable'
                is_sec = el.get('status') == 'secure'
                fill = "#fee2e2" if is_vuln else ("#dcfce7" if is_sec else "#eff6ff")
                stroke = "#dc2626" if is_vuln else ("#16a34a" if is_sec else "#2563eb")
                color = "#991b1b" if is_vuln else ("#166534" if is_sec else "#1e40af")
                pid = el.get('id', '')
                badge_str = f" <span style='font-size:9px;'>[{badge}]</span>" if badge else ""
                inner = f"<b style='color:{color};font-size:11px;'>ПРОЦЕСС {pid}{badge_str}</b><br><b style='font-size: 12px;'>{title}</b><br><font style='font-size: 10px; color: #334155;'>{sub}</font>"
                style = f"shape=rect;rounded=1;arcSize=15;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};strokeWidth=2;fontColor=#0f172a;align=center;verticalAlign=top;spacingTop=6;"
            elif t == 'store':
                sid = el.get('id', '')
                is_vuln = el.get('status') == 'vulnerable'
                is_sec = el.get('status') == 'secure'
                stroke = "#dc2626" if is_vuln else ("#16a34a" if is_sec else "#475569")
                fill = "#fff1f2" if is_vuln else ("#f0fdf4" if is_sec else "#f8fafc")
                badge_str = f" <span style='font-size:9px;'>[{badge}]</span>" if badge else ""
                inner = f"<b style='color:{stroke};'>[{sid}] {title}</b>{badge_str}<br><font style='font-size: 10px; color: #475569;'>{sub}</font>"
                style = f"shape=partialRectangle;top=1;bottom=1;left=1;right=0;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};strokeWidth=2;fontColor=#0f172a;align=left;spacingLeft=12;"
            elif t == 'security_badge':
                inner = f"<b style='color:#15803d;font-size:11px;'>🛡️ {title}</b><br><font style='font-size: 9px; color: #166534;'>{sub}</font>"
                style = "shape=rectangle;rounded=1;dashed=1;dashPattern=4 2;whiteSpace=wrap;html=1;fillColor=#f0fdf4;strokeColor=#16a34a;strokeWidth=1.5;fontColor=#14532d;align=left;verticalAlign=top;spacingLeft=8;spacingTop=6;"

            val = xml_attr_escape(inner)
            xml_lines.append(f'        <mxCell id="{cid}" value="{val}" style="{style}" vertex="1" parent="1">')
            xml_lines.append(f'          <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />')
            xml_lines.append('        </mxCell>')

        # Draw flows as connectors
        for fl_idx, fl in enumerate(diag['flows'], start=1):
            fid = f"flow_{diag_id}_{fl_idx}"
            fx, fy = fl['from_pt']
            tx, ty = fl['to_pt']
            lbl = xml_attr_escape(fl['label'])
            st = fl.get('style', 'normal')
            
            color = "#dc2626" if st == 'vulnerable' else ("#16a34a" if st == 'secure' else "#475569")
            style = f"edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor={color};strokeWidth=1.5;fontColor={color};fontSize=10;fontStyle=1;labelBackgroundColor=#ffffff;"
            
            xml_lines.append(f'        <mxCell id="{fid}" value="{lbl}" style="{style}" edge="1" parent="1">')
            xml_lines.append(f'          <mxGeometry relative="1" as="geometry">')
            xml_lines.append(f'            <mxPoint x="{fx}" y="{fy}" as="sourcePoint" />')
            xml_lines.append(f'            <mxPoint x="{tx}" y="{ty}" as="targetPoint" />')
            xml_lines.append('          </mxGeometry>')
            xml_lines.append('        </mxCell>')

        xml_lines.append('      </root>')
        xml_lines.append('    </mxGraphModel>')
        xml_lines.append('  </diagram>')

    xml_lines.append('</mxfile>')

    with open(DRAWIO_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml_lines))
    print(f"Generated draw.io XML: {DRAWIO_PATH}")

if __name__ == '__main__':
    generate_drawio()
