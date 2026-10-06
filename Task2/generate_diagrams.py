#!/usr/bin/env python3
"""Build matching C4 SVG and editable draw.io views using Graphviz layout."""
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
COLORS = {"person": "#123b60", "system": "#64748b", "main": "#1565a7",
          "container": "#dceeff", "security": "#dcfce7", "analytics": "#ede9fe"}


def node(key, title, kind, description, tech=""):
    label = f"{title}\n[{kind}]" + (f"\n{tech}" if tech else "") + f"\n{description}"
    return key, label


PEOPLE = [node("patient", "Пациент", "Person", "Свои записи и документы"),
          node("staff", "Персонал клиники", "Person", "Ресепшен, врач, кассир"),
          node("analyst", "Аналитик", "Person", "Утверждённые наборы")]
EXTERNAL = [node("ad", "Active Directory", "Software System", "Каталог сотрудников"),
            node("lab", "Лаборатория", "Software System", "Заказы и результаты"),
            node("bank", "Эквайринг", "Software System", "Приём оплаты"),
            node("accounting", "1С:Бухгалтерия", "Software System", "Учёт и кадры"),
            node("stock", "1С:Торговля и склад", "Software System", "ТМЦ и закупки"),
            node("kkm", "ККМ", "Software System", "Фискализация"),
            node("notify", "Доставка уведомлений", "Software System", "Почта / push / голос")]


def context():
    nodes = dict(PEOPLE + EXTERNAL + [
        node("platform", "Медицинская платформа", "Software System",
             "Запись, профиль, карта, оплата;\nзащита данных и аналитика"),
        node("finance", "Бухгалтер", "Person", "Учёт в 1С"),
        node("storekeeper", "Сотрудник склада", "Person", "Учёт ТМЦ")])
    styles = {k: "person" for k in ["patient", "staff", "analyst", "finance", "storekeeper"]}
    styles.update({k: "system" for k, _ in EXTERNAL})
    styles["platform"] = "main"
    edges = [("patient", "platform", "Записывается; читает своё"),
             ("staff", "platform", "Работает по роли и цели"),
             ("analyst", "platform", "Использует разрешённые витрины"),
             ("platform", "ad", "Проверяет учётные записи"),
             ("platform", "lab", "Минимальные заказы; результаты"),
             ("platform", "bank", "Создаёт оплату; получает статус"),
             ("platform", "accounting", "Передаёт учётные документы"),
             ("platform", "kkm", "Запрашивает чек через адаптер"),
             ("platform", "notify", "Передаёт нейтральное уведомление"),
             ("finance", "accounting", "Ведёт учёт"),
             ("storekeeper", "stock", "Ведёт складской учёт"),
             ("stock", "accounting", "Передаёт учётные сведения")]
    return "C4 — контекст целевого состояния", nodes, styles, edges, [], "LR"


def containers():
    internal = [
        node("web", "Порталы", "Container", "Интерфейсы пациента и персонала", "Web"),
        node("mobile", "Мобильный клиент", "Container", "Запись и свои документы", "Mobile"),
        node("gateway", "API-шлюз", "Container", "Вход, токены, лимиты", "Kong / HTTPS"),
        node("app", "Клиническое приложение", "Container", "Профиль / CRM, запись, карта,\nоснования обработки, оплата", "Java / доменные модули"),
        node("db", "Операционная БД", "Container", "Доменные схемы, RLS, outbox;\nсоответствие лабораторных токенов", "PostgreSQL / шифрование тома"),
        node("docs", "Документы", "Container", "Заключения, анализы, договоры", "S3 / шифрование и версии"),
        node("worker", "Адаптеры и фоновые операции", "Container", "Минимальные контракты;\nповторы без дублирования", "Java / outbox"),
        node("iam", "Идентификация", "Container", "Вход, MFA, отзыв сессий", "Keycloak"),
        node("opa", "Политики доступа", "Container", "Роли, филиал, объект, цель;\nлокальный пакет в приложении", "OPA"),
        node("vault", "Ключи и секреты", "Container", "Выдача по сервисной роли", "Vault / KMS"),
        node("audit", "Аудит и оповещения", "Container", "Чтения, изменения, отклонения;\nзащищённое хранение событий", "Сборщик / поиск / архив"),
        node("catalog", "Каталог метаданных", "Container", "Классы, владельцы, сроки;\nпроисхождение наборов", "OpenMetadata"),
        node("pipeline", "Конвейер приватности", "Container", "Классификация, минимизация,\nпроверка и карантин", "Пакетная обработка / CDC"),
        node("lake", "Защищённое озеро", "Container", "Исходная закрытая зона;\nпроверенная зона отдельно", "S3 / ключи по зонам"),
        node("warehouse", "Аналитическая БД", "Container", "Утверждённые витрины", "ClickHouse"),
        node("bi", "BI-интерфейс", "Container", "Отчёты и агрегаты", "Superset"),
        node("ml", "Рабочее место ML / AI", "Container", "Только разрешённые наборы;\nпроверка моделей", "Серверная среда")]
    nodes = dict(PEOPLE + EXTERNAL + internal + [
        node("legacy", "Файловый архив", "Software System", "Зарегистрированные импорты")])
    styles = {k: "person" for k, _ in PEOPLE}
    styles.update({k: "system" for k, _ in EXTERNAL + [("legacy", "")]})
    styles.update({k: "container" for k, _ in internal})
    styles.update({k: "security" for k in ["iam", "opa", "vault", "audit", "catalog"]})
    styles.update({k: "analytics" for k in ["pipeline", "lake", "warehouse", "bi", "ml"]})
    edges = [
        ("patient", "web", "Свои данные"), ("patient", "mobile", "Свои данные"),
        ("staff", "web", "По роли"),
        ("web", "gateway", "HTTPS / API"), ("mobile", "gateway", "HTTPS / API"),
        ("gateway", "app", "TLS / проверенный запрос"),
        ("web", "iam", "Вход / OIDC", "control"),
        ("mobile", "iam", "Вход / OIDC", "control"),
        ("iam", "ad", "LDAPS / сотрудники", "control"),
        ("app", "iam", "Токен / статус доступа", "control"),
        ("app", "opa", "Пакет правил доступа", "control"),
        ("app", "vault", "TLS / ключи и секреты", "control"),
        ("app", "audit", "События доступа", "control"),
        ("app", "db", "TLS / доменные роли"),
        ("app", "docs", "TLS / разрешённый объект"),
        ("worker", "db", "TLS / читает outbox"),
        ("worker", "app", "TLS / результат операции"),
        ("worker", "lab", "mTLS / токен заказа"),
        ("worker", "bank", "HTTPS / заказ и статус"),
        ("worker", "accounting", "TLS / учётные документы"),
        ("worker", "kkm", "Выделенный канал / чек"),
        ("worker", "notify", "TLS / контакт и шаблон"),
        ("stock", "accounting", "Учёт ТМЦ"),
        ("pipeline", "db", "TLS / разрешённая выгрузка"),
        ("pipeline", "legacy", "Защищённый импорт"),
        ("pipeline", "catalog", "Схемы, теги, происхождение", "control"),
        ("pipeline", "vault", "TLS / ключи зон", "control"),
        ("pipeline", "audit", "Результаты проверки", "control"),
        ("pipeline", "lake", "TLS / раздельные зоны"),
        ("pipeline", "warehouse", "TLS / проверенные витрины"),
        ("analyst", "bi", "Отчёты"), ("analyst", "ml", "Разрешённые эксперименты"),
        ("bi", "warehouse", "TLS / чтение витрин"),
        ("ml", "lake", "TLS / проверенная зона")]
    return "C4 — контейнеры целевого состояния", nodes, styles, edges, [k for k, _ in internal], "LR"


def dot_source(spec):
    title, nodes, styles, edges, internal, direction = spec
    lines = ['digraph G {', f'rankdir={direction};',
             'graph [fontname="DejaVu Sans", fontsize=22, bgcolor="white", nodesep=0.6, ranksep=0.8, pad=0.4, compound=true];',
             'node [shape=box, style="rounded,filled", fontname="DejaVu Sans", fontsize=13, margin="0.20,0.16", penwidth=1.3];',
             'edge [fontname="DejaVu Sans", fontsize=11, color="#475569", arrowsize=0.7];',
             f'label={json.dumps(title, ensure_ascii=False)}; labelloc=t;']

    def declaration(key):
        color = COLORS[styles[key]]
        dark = styles[key] in ["person", "system", "main"]
        return f'{key} [label={json.dumps(nodes[key], ensure_ascii=False)}, fillcolor="{color}", color="{color if dark else "#64748b"}", fontcolor="{"white" if dark else "#172554"}"];'

    for key in nodes:
        if key not in internal:
            lines.append(declaration(key))
    if internal:
        lines.append('subgraph cluster_platform { label="Медицинская платформа — граница системы"; style="rounded,dashed"; color="#94a3b8"; fontsize=18;')
        lines.extend(declaration(key) for key in internal)
        lines.append('}')
    for edge in edges:
        source, target, label, *flags = edge
        control = bool(flags)
        lines.append(f'{source} -> {target} [label={json.dumps(label, ensure_ascii=False)}, style="{"dashed" if control else "solid"}", constraint={"false" if control else "true"}, color="{"#15803d" if control else "#475569"}"];')
    lines.append('legend [shape=plain, style="", fillcolor="white", label="Легенда: тёмно-синий — человек; серый — другая система; синий — платформа / приложение;\nзелёный — управление защитой; фиолетовый — аналитика. Стрелка: инициатор → получатель; ответ подразумевается.\nПунктирная связь — управление защитой; пунктирная рамка — граница платформы. Размещение серверов не показано.", fontsize=12, fontcolor="#334155"];')
    lines.append('}')
    return '\n'.join(lines)


def drawio_page(mxfile, spec, layout, page_id):
    title, nodes, styles, edges, internal, _ = spec
    bb = [float(v) for v in layout['bb'].split(',')]
    height = bb[3]
    margin, header = 40, 70
    diagram = ET.SubElement(mxfile, 'diagram', id=page_id, name=title)
    model = ET.SubElement(diagram, 'mxGraphModel', grid='1', gridSize='10',
                          page='1', pageWidth=str(int(bb[2] + 2 * margin)),
                          pageHeight=str(int(height + header + 2 * margin)))
    root = ET.SubElement(model, 'root')
    ET.SubElement(root, 'mxCell', id='0')
    ET.SubElement(root, 'mxCell', id='1', parent='0')

    def rect(key, label, x, y, w, h, style):
        cell = ET.SubElement(root, 'mxCell', id=key, value=label, vertex='1', parent='1', style=style)
        ET.SubElement(cell, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), **{'as': 'geometry'})

    rect('title', title, margin, 10, bb[2], 45,
         'text;html=0;align=center;fontSize=22;fontStyle=1;')
    for obj in layout['objects']:
        if 'bb' in obj:
            x1, y1, x2, y2 = map(float, obj['bb'].split(','))
            rect(obj['name'], obj.get('label', ''), x1 + margin, height - y2 + header,
                 x2 - x1, y2 - y1, 'rounded=1;dashed=1;fillColor=none;strokeColor=#94a3b8;verticalAlign=top;align=left;spacing=8;fontSize=18;')
    for obj in layout['objects']:
        if 'pos' not in obj:
            continue
        key = obj['name']
        x, y = map(float, obj['pos'].split(','))
        w, h = float(obj['width']) * 72, float(obj['height']) * 72
        color = COLORS[styles[key]] if key in styles else '#ffffff'
        dark = key in styles and styles[key] in ['person', 'system', 'main']
        style = f'rounded=1;whiteSpace=wrap;html=0;fillColor={color};strokeColor=#64748b;fontColor={"#ffffff" if dark else "#172554"};fontSize={13 if key in nodes else 12};'
        rect(key, nodes.get(key, obj.get('label', '')), x - w/2 + margin,
             height - y - h/2 + header, w, h, style)
    names = {o['_gvid']: o['name'] for o in layout['objects']}
    for idx, edge in enumerate(layout['edges']):
        control = edge.get('style') == 'dashed'
        cell = ET.SubElement(root, 'mxCell', id=f'edge{idx}', edge='1', parent='1',
                             source=names[edge['tail']], target=names[edge['head']],
                             style=f'endArrow=block;html=0;strokeColor={"#15803d" if control else "#475569"};dashed={int(control)};')
        geo = ET.SubElement(cell, 'mxGeometry', relative='1', **{'as': 'geometry'})
        # Graphviz bezier points become an editable polyline in diagrams.net.
        points = []
        for item in edge.get('pos', '').split():
            coords = item.split(',')
            if len(coords) == 2:
                points.append(tuple(map(float, coords)))
        array = ET.SubElement(geo, 'Array', **{'as': 'points'})
        for x, y in points[1:-1]:
            ET.SubElement(array, 'mxPoint', x=str(x + margin), y=str(height - y + header))
        if 'lp' in edge:
            x, y = map(float, edge['lp'].split(','))
            label = edge['label']
            w = max(len(part) for part in label.split('\n')) * 8 + 12
            rect(f'label{idx}', label, x - w/2 + margin, height - y - 11 + header,
                 w, 24, 'text;html=0;whiteSpace=wrap;fontSize=11;fillColor=#ffffff;strokeColor=none;')


def main():
    target = BASE / 'diagrams'
    target.mkdir(exist_ok=True)
    mxfile = ET.Element('mxfile', host='app.diagrams.net', version='24.7.5')
    for slug, spec in [('c4-context', context()), ('c4-containers', containers())]:
        source = dot_source(spec)
        svg = subprocess.run(['dot', '-Tsvg'], input=source, text=True, capture_output=True, check=True).stdout
        (target / f'{slug}.svg').write_text(svg, encoding='utf-8')
        layout = json.loads(subprocess.run(['dot', '-Tjson'], input=source, text=True, capture_output=True, check=True).stdout)
        drawio_page(mxfile, spec, layout, slug)
    ET.indent(mxfile)
    ET.ElementTree(mxfile).write(BASE / 'medikamente-target.drawio', encoding='utf-8', xml_declaration=True)


if __name__ == '__main__':
    main()
