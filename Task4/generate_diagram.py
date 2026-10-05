#!/usr/bin/env python3
"""Generate a true editable fishbone and matching standalone SVG (stdlib only)."""
from pathlib import Path
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
WIDTH, HEIGHT = 2280, 1360
CATEGORIES = [
    ("Инфраструктура", "#0369a1", [
        ("INF-01", "Конкуренция служб одного сервера"),
        ("INF-02", "Ограничения каналов филиалов"),
        ("INF-03", "Зависимость восстановления от узла")]),
    ("Данные", "#7c3aed", [
        ("DAT-01", "Дубли и несвязанные документы"),
        ("DAT-02", "Большой импорт и временные файлы"),
        ("DAT-03", "Изменения источника при переносе")]),
    ("Интеграции", "#0f766e", [
        ("INT-01", "Блокировки файловой 1С / ККМ"),
        ("INT-02", "Таймауты, лимиты и повторы API"),
        ("INT-03", "Избыточные / несовместимые события")]),
    ("Приложение и защита", "#b45309", [
        ("APP-01", "Индексы и конфликтующие брони"),
        ("APP-02", "Синхронные зависимости защиты"),
        ("APP-03", "Дробление сервисов / тяжёлые отчёты")]),
    ("Персонал", "#be185d", [
        ("PEO-01", "Недостаток владельцев и дежурства"),
        ("PEO-02", "Привычный ввод в старые Excel"),
        ("PEO-03", "Ошибки назначения прав и обучения")]),
    ("Процессы и контроль", "#4338ca", [
        ("PRO-01", "Нет исходных метрик и оповещений"),
        ("PRO-02", "Непроверенная заморозка / возврат"),
        ("PRO-03", "Несколько изменений одновременно")])]


def build():
    svg = ET.Element('svg', xmlns='http://www.w3.org/2000/svg', width=str(WIDTH),
                     height=str(HEIGHT), viewBox=f'0 0 {WIDTH} {HEIGHT}')
    ET.SubElement(svg, 'title').text = 'Исикава: причины деградации при миграции Медикаменте'
    ET.SubElement(svg, 'desc').text = 'Шесть категорий, восемнадцать причин; идентификаторы связаны с реестром migration-risks.md.'
    ET.SubElement(svg, 'rect', width=str(WIDTH), height=str(HEIGHT), fill='#ffffff')
    defs = ET.SubElement(svg, 'defs')
    marker = ET.SubElement(defs, 'marker', id='arrow', markerWidth='10', markerHeight='10',
                           refX='9', refY='5', orient='auto')
    ET.SubElement(marker, 'path', d='M0,0 L10,5 L0,10 Z', fill='#334155')
    mxfile = ET.Element('mxfile', host='app.diagrams.net', version='24.7.5')
    diagram = ET.SubElement(mxfile, 'diagram', id='ishikawa', name='Причины деградации при миграции')
    model = ET.SubElement(diagram, 'mxGraphModel', grid='1', gridSize='10', page='1',
                          pageWidth=str(WIDTH), pageHeight=str(HEIGHT))
    root = ET.SubElement(model, 'root')
    ET.SubElement(root, 'mxCell', id='0')
    ET.SubElement(root, 'mxCell', id='1', parent='0')

    def text_box(key, text, x, y, w, h, size=18, color='#172554', fill='none', bold=False):
        if fill != 'none':
            ET.SubElement(svg, 'rect', x=str(x), y=str(y), width=str(w), height=str(h),
                          fill=fill, stroke=color, rx='10', **{'stroke-width': '2'})
        text_el = ET.SubElement(svg, 'text', x=str(x+12), y=str(y+size+8), fill=color,
                               **{'font-family':'DejaVu Sans, sans-serif', 'font-size':str(size),
                                  'font-weight':'bold' if bold else 'normal'})
        for i, part in enumerate(text.split('\n')):
            span = ET.SubElement(text_el, 'tspan', x=str(x+12), dy='0' if i==0 else str(size+7))
            span.text = part
        style = f'rounded=1;whiteSpace=wrap;html=0;align=left;verticalAlign=top;spacing=12;fillColor={fill};strokeColor={color if fill != "none" else "none"};fontColor={color};fontSize={size};fontStyle={int(bold)};'
        cell = ET.SubElement(root, 'mxCell', id=key, value=text, style=style, vertex='1', parent='1')
        ET.SubElement(cell, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), **{'as':'geometry'})

    def line(key, x1, y1, x2, y2, color='#334155', width=2, arrow=False):
        attrs = {'x1':str(x1), 'y1':str(y1), 'x2':str(x2), 'y2':str(y2),
                 'stroke':color, 'stroke-width':str(width)}
        if arrow: attrs['marker-end'] = 'url(#arrow)'
        ET.SubElement(svg, 'line', **attrs)
        cell = ET.SubElement(root, 'mxCell', id=key, edge='1', parent='1',
                             style=f'endArrow={"block" if arrow else "none"};strokeColor={color};strokeWidth={width};')
        geo = ET.SubElement(cell, 'mxGeometry', relative='1', **{'as':'geometry'})
        ET.SubElement(geo, 'mxPoint', x=str(x1), y=str(y1), **{'as':'sourcePoint'})
        ET.SubElement(geo, 'mxPoint', x=str(x2), y=str(y2), **{'as':'targetPoint'})

    text_box('title', 'МЕДИКАМЕНТЕ · Причины деградации при миграции', 65, 25, 2100, 55, 30, bold=True)
    text_box('subtitle', 'Диаграмма Исикавы: факты исходного устройства и проверяемые гипотезы. Коды раскрыты в реестре рисков.',
             65, 85, 2150, 50, 19, '#475569')
    line('spine', 70, 680, 2010, 680, width=5, arrow=True)
    text_box('effect', 'Деградация\nобслуживания\nпри миграции\nи росте данных',
             2020, 584, 235, 190, 21, '#991b1b', '#fff1f2', True)
    for index, (title, color, causes) in enumerate(CATEGORIES):
        col, bottom = index % 3, index >= 3
        start = 70 + 620*col
        x1, y1 = start+430, 1140 if bottom else 220
        x2, y2 = start+550, 680
        text_box(f'category{index}', title, start, 1185 if bottom else 145, 510, 64,
                 23, color, '#f8fafc', True)
        line(f'bone{index}', x1, y1, x2, y2, color, 4)
        for j, (key, cause) in enumerate(causes):
            y = (790+120*j) if bottom else (290+120*j)
            branch_y = y+78
            branch_x = x1+(x2-x1)*(branch_y-y1)/(y2-y1)
            text_box(key, f'{key}\n{cause}', start+8, y, 430, 70, 18, '#172554')
            line(f'leaf{key}', start+18, branch_y, branch_x, branch_y, color, 2)
    text_box('legend', 'Главная ось → последствие. Наклонные ветви → категории. Горизонтальные ветви → возможные причины.\nНаличие причины не означает измеренную деградацию; подтверждение и приоритет мер — в migration-risks.md.',
             65, 1290, 2160, 60, 18, '#475569')
    return svg, mxfile


def main():
    svg, mxfile = build()
    (BASE / 'diagrams').mkdir(exist_ok=True)
    for element, path in [(svg, BASE/'diagrams/migration-ishikawa.svg'),
                          (mxfile, BASE/'migration-ishikawa.drawio')]:
        ET.indent(element)
        ET.ElementTree(element).write(path, encoding='utf-8', xml_declaration=True)


if __name__ == '__main__':
    main()
