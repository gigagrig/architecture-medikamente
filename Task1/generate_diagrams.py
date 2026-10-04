#!/usr/bin/env python3
"""
Generator for Data Flow Diagrams (DFD) As-Is and To-Be for Medikamente architecture.
Produces 12 standalone SVG files and a combined multi-page draw.io file.
"""

import os
import xml.etree.ElementTree as ET

DIAGRAMS_DIR = os.path.join(os.path.dirname(__file__), "diagrams")
os.makedirs(DIAGRAMS_DIR, exist_ok=True)

def create_svg(width, height, title, subtitle, elements, flows):
    """
    elements: list of dicts:
      type: 'entity' | 'process' | 'store' | 'security_badge'
      id, x, y, w, h, title, subtitle, color_scheme
    flows: list of dicts:
      from_pt: (x, y), to_pt: (x, y), label: str, style: 'normal'|'vulnerable'|'secure'
    """
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" style="background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif;">',
        '  <defs>',
        '    <marker id="arrow-default" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '      <path d="M 0 1 L 10 5 L 0 9 z" fill="#475569" />',
        '    </marker>',
        '    <marker id="arrow-vulnerable" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '      <path d="M 0 1 L 10 5 L 0 9 z" fill="#dc2626" />',
        '    </marker>',
        '    <marker id="arrow-secure" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '      <path d="M 0 1 L 10 5 L 0 9 z" fill="#16a34a" />',
        '    </marker>',
        '    <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%" filterUnits="userSpaceOnUse">',
        '      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.08"/>',
        '    </filter>',
        '  </defs>',
        '',
        '  <!-- Header -->',
        f'  <rect x="0" y="0" width="{width}" height="60" fill="#1e293b"/>',
        f'  <text x="25" y="32" font-size="18" font-weight="bold" fill="#ffffff">{title}</text>',
        f'  <text x="25" y="50" font-size="12" fill="#94a3b8">{subtitle}</text>',
        ''
    ]

    # Draw Elements
    for el in elements:
        t = el.get('type')
        x, y, w, h = el['x'], el['y'], el['w'], el['h']
        name = el['title']
        sub = el.get('subtitle', '')
        badge = el.get('badge', '')
        
        if t == 'entity':
            # External Entity: Solid rectangle with double-line or distinct header
            svg.append(f'  <!-- External Entity: {name} -->')
            svg.append(f'  <g filter="url(#shadow)">')
            svg.append(f'    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#ffffff" stroke="#0284c7" stroke-width="2"/>')
            svg.append(f'    <rect x="{x}" y="{y}" width="{w}" height="24" rx="4" fill="#0284c7"/>')
            svg.append(f'    <text x="{x + w/2}" y="{y + 16}" font-size="11" font-weight="bold" fill="#ffffff" text-anchor="middle">ВНЕШНЯЯ СУЩНОСТЬ</text>')
            svg.append(f'    <text x="{x + w/2}" y="{y + 45}" font-size="13" font-weight="bold" fill="#0f172a" text-anchor="middle">{name}</text>')
            if sub:
                svg.append(f'    <text x="{x + w/2}" y="{y + 63}" font-size="10" fill="#64748b" text-anchor="middle">{sub}</text>')
            svg.append(f'  </g>')

        elif t == 'process':
            # Process: Rounded rectangle with ID top bar
            is_vuln = el.get('status') == 'vulnerable'
            is_sec = el.get('status') == 'secure'
            stroke_col = "#dc2626" if is_vuln else ("#16a34a" if is_sec else "#2563eb")
            header_col = "#fee2e2" if is_vuln else ("#dcfce7" if is_sec else "#eff6ff")
            text_col = "#991b1b" if is_vuln else ("#166534" if is_sec else "#1e40af")
            
            pid = el.get('id', '1.0')
            svg.append(f'  <!-- Process {pid}: {name} -->')
            svg.append(f'  <g filter="url(#shadow)">')
            svg.append(f'    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#ffffff" stroke="{stroke_col}" stroke-width="2"/>')
            svg.append(f'    <path d="M {x} {y+24} L {x+w} {y+24}" stroke="{stroke_col}" stroke-width="1"/>')
            svg.append(f'    <rect x="{x+1}" y="{y+1}" width="{w-2}" height="23" rx="11" fill="{header_col}"/>')
            svg.append(f'    <text x="{x+12}" y="{y+16}" font-size="11" font-weight="bold" fill="{text_col}">ПРОЦЕСС {pid}</text>')
            if badge:
                svg.append(f'    <text x="{x+w-12}" y="{y+16}" font-size="10" font-weight="bold" fill="{text_col}" text-anchor="end">{badge}</text>')
            svg.append(f'    <text x="{x + w/2}" y="{y + 46}" font-size="12" font-weight="bold" fill="#0f172a" text-anchor="middle">{name}</text>')
            if sub:
                # support multi-line sub
                lines = sub.split('\n')
                sy = y + 64
                for line in lines:
                    svg.append(f'    <text x="{x + w/2}" y="{sy}" font-size="10" fill="#475569" text-anchor="middle">{line}</text>')
                    sy += 14
            svg.append(f'  </g>')

        elif t == 'store':
            # Data Store: Open-ended rectangle (Gane-Sarson / DeMarco)
            sid = el.get('id', 'D1')
            is_vuln = el.get('status') == 'vulnerable'
            is_sec = el.get('status') == 'secure'
            stroke_col = "#dc2626" if is_vuln else ("#16a34a" if is_sec else "#475569")
            bg_col = "#fff1f2" if is_vuln else ("#f0fdf4" if is_sec else "#f8fafc")
            
            svg.append(f'  <!-- Data Store {sid}: {name} -->')
            svg.append(f'  <g filter="url(#shadow)">')
            svg.append(f'    <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{bg_col}" stroke="none"/>')
            svg.append(f'    <line x1="{x}" y1="{y}" x2="{x+w}" y2="{y}" stroke="{stroke_col}" stroke-width="2"/>')
            svg.append(f'    <line x1="{x}" y1="{y+h}" x2="{x+w}" y2="{y+h}" stroke="{stroke_col}" stroke-width="2"/>')
            svg.append(f'    <line x1="{x}" y1="{y}" x2="{x}" y2="{y+h}" stroke="{stroke_col}" stroke-width="2"/>')
            svg.append(f'    <line x1="{x+36}" y1="{y}" x2="{x+36}" y2="{y+h}" stroke="{stroke_col}" stroke-width="1.5"/>')
            svg.append(f'    <text x="{x+18}" y="{y+h/2+4}" font-size="11" font-weight="bold" fill="{stroke_col}" text-anchor="middle">{sid}</text>')
            svg.append(f'    <text x="{x+46}" y="{y+20}" font-size="12" font-weight="bold" fill="#0f172a">{name}</text>')
            if sub:
                lines = sub.split('\n')
                sy = y + 36
                for line in lines:
                    svg.append(f'    <text x="{x+46}" y="{sy}" font-size="10" fill="#64748b">{line}</text>')
                    sy += 13
            if badge:
                svg.append(f'    <rect x="{x+w-70}" y="{y+4}" width="65" height="18" rx="3" fill="{stroke_col}" fill-opacity="0.1"/>')
                svg.append(f'    <text x="{x+w-37}" y="{y+17}" font-size="9" font-weight="bold" fill="{stroke_col}" text-anchor="middle">{badge}</text>')
            svg.append(f'  </g>')

        elif t == 'security_badge':
            # Security Control box in To-Be
            svg.append(f'  <!-- Security Control: {name} -->')
            svg.append(f'  <g>')
            svg.append(f'    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5" stroke-dasharray="4 2"/>')
            svg.append(f'    <text x="{x+w/2}" y="{y+16}" font-size="10" font-weight="bold" fill="#15803d" text-anchor="middle">{name}</text>')
            if sub:
                lines = sub.split('\n')
                sy = y + 30
                for line in lines:
                    svg.append(f'    <text x="{x+w/2}" y="{sy}" font-size="9" fill="#166534" text-anchor="middle">{line}</text>')
                    sy += 12
            svg.append(f'  </g>')

    # Draw Flows
    for fl in flows:
        fx, fy = fl['from_pt']
        tx, ty = fl['to_pt']
        lbl = fl['label']
        st = fl.get('style', 'normal')
        
        marker = 'arrow-default'
        color = '#475569'
        dash = ''
        if st == 'vulnerable':
            marker = 'arrow-vulnerable'
            color = '#dc2626'
        elif st == 'secure':
            marker = 'arrow-secure'
            color = '#16a34a'
        elif st == 'dashed':
            dash = 'stroke-dasharray="4 3"'
            
        points = fl.get('points')
        if points:
            d = f"M {points[0][0]} {points[0][1]} "
            for pt in points[1:]:
                d += f"L {pt[0]} {pt[1]} "
            svg.append(f'  <path d="{d}" fill="none" stroke="{color}" stroke-width="1.5" {dash} marker-end="url(#{marker})"/>')
            # label position
            lx, ly = fl.get('lbl_pt', (points[0][0] + points[-1][0])/2, (points[0][1] + points[-1][1])/2)
        else:
            svg.append(f'  <line x1="{fx}" y1="{fy}" x2="{tx}" y2="{ty}" stroke="{color}" stroke-width="1.5" {dash} marker-end="url(#{marker})"/>')
            lx = (fx + tx) / 2
            ly = (fy + ty) / 2
            if 'lbl_offset' in fl:
                lx += fl['lbl_offset'][0]
                ly += fl['lbl_offset'][1]

        # Draw label box
        lbl_lines = lbl.split('\n')
        line_count = len(lbl_lines)
        max_len = max(len(l) for l in lbl_lines)
        rect_w = max(60, max_len * 6.5 + 10)
        rect_h = line_count * 13 + 6
        
        svg.append(f'  <rect x="{lx - rect_w/2}" y="{ly - rect_h/2}" width="{rect_w}" height="{rect_h}" rx="3" fill="#ffffff" fill-opacity="0.95" stroke="{color}" stroke-width="0.75"/>')
        
        start_y = ly - (line_count - 1) * 6 + 3
        for l in lbl_lines:
            svg.append(f'  <text x="{lx}" y="{start_y}" font-size="9.5" fill="{color}" font-weight="600" text-anchor="middle">{l}</text>')
            start_y += 12

    svg.append('</svg>')
    return '\n'.join(svg)


# --------------------------------------------------------------------------
# Definitions for all 6 processes
# --------------------------------------------------------------------------

# Process 1: Регистрация пациента
p1_as_is = {
    'width': 920, 'height': 520,
    'title': 'DFD Процесс 1 (As-Is): Первичная регистрация пациента и оформление документов',
    'subtitle': 'Текущее состояние: ручной сбор избыточных ПДн, хранение сканов на общем сетевом диске без шифрования и разграничения прав',
    'elements': [
        {'type': 'entity', 'id': 'E1', 'x': 40, 'y': 100, 'w': 180, 'h': 85, 'title': 'Пациент (Patient)', 'subtitle': 'Субъект ПДн\nОчное обращение'},
        {'type': 'entity', 'id': 'E2', 'x': 40, 'y': 280, 'w': 180, 'h': 85, 'title': 'Ресепшен (Receptionist)', 'subtitle': 'Сотрудник клиники\n3 человека'},
        {'type': 'process', 'id': '1.1', 'x': 290, 'y': 95, 'w': 220, 'h': 95, 'title': 'Сбор ПДн и анкеты', 'subtitle': 'Ручное заполнение бланка:\nпаспорт, контакты, работа,\nхронические заболевания', 'status': 'vulnerable', 'badge': 'Избыточный сбор'},
        {'type': 'process', 'id': '1.2', 'x': 290, 'y': 230, 'w': 220, 'h': 95, 'title': 'Ведение Excel-реестра', 'subtitle': 'Внесение данных пациента\nв единый неструктурированный\nфайл Patients.xlsx', 'status': 'vulnerable', 'badge': 'Нет контроля прав'},
        {'type': 'process', 'id': '1.3', 'x': 290, 'y': 365, 'w': 220, 'h': 95, 'title': 'Сканирование документов', 'subtitle': 'МФУ -> скан паспорта,\nдоговора и согласия\nв JPG / PDF без учета', 'status': 'vulnerable', 'badge': 'Теневые сканы'},
        {'type': 'store', 'id': 'D1', 'x': 600, 'y': 150, 'w': 280, 'h': 90, 'title': 'Файловый диск: Patients.xlsx', 'subtitle': 'Общий каталог SMB/CIFS\nДоступен всем доменным пользователям\nОтсутствует шифрование и аудит', 'status': 'vulnerable', 'badge': 'Риск УЗ-1'},
        {'type': 'store', 'id': 'D2', 'x': 600, 'y': 330, 'w': 280, 'h': 105, 'title': 'Файловый диск: \\\\Pacients\\*', 'subtitle': 'Папки: Pacient1-FIO-BD\nСканы паспортов, согласий, анкет\nНет версионирования и удаления', 'status': 'vulnerable', 'badge': 'Нарушение 152-ФЗ'}
    ],
    'flows': [
        {'from_pt': (220, 135), 'to_pt': (290, 135), 'label': 'Бумажная анкета:\nФИО, паспорт, телефон,\nместо работы/учебы, анамнез', 'style': 'vulnerable'},
        {'from_pt': (130, 280), 'to_pt': (130, 185), 'label': 'Выдача бланков\nи договоров', 'style': 'normal'},
        {'from_pt': (220, 310), 'to_pt': (290, 280), 'label': 'Ручной ввод\nФИО и контактов', 'style': 'normal'},
        {'from_pt': (220, 340), 'to_pt': (290, 400), 'label': 'Сканирование\nдокументов на МФУ', 'style': 'normal'},
        {'from_pt': (510, 260), 'to_pt': (600, 200), 'label': 'Запись строки\nв открытый Excel', 'style': 'vulnerable'},
        {'from_pt': (510, 410), 'to_pt': (600, 380), 'label': 'Сохранение JPG/PDF\nпо SMB без шифрования', 'style': 'vulnerable'}
    ]
}

p1_to_be = {
    'width': 980, 'height': 560,
    'title': 'DFD Процесс 1 (To-Be): Защищенная регистрация и онбординг пациента',
    'subtitle': 'Целевое состояние: Data Minimization, TLS 1.3, Keycloak RBAC/ABAC, PostgreSQL TDE, MinIO S3 SSE-KMS, тегирование PII',
    'elements': [
        {'type': 'entity', 'id': 'E1', 'x': 30, 'y': 100, 'w': 170, 'h': 85, 'title': 'Пациент (Client)', 'subtitle': 'Web-портал / App / Планшет\nСамостоятельный ввод'},
        {'type': 'entity', 'id': 'E2', 'x': 30, 'y': 280, 'w': 170, 'h': 85, 'title': 'Ресепшен (Staff)', 'subtitle': 'АРМ сотрудника ресепшена\nРоль: Receptionist (RBAC)'},
        {'type': 'process', 'id': '1.1', 'x': 250, 'y': 95, 'w': 220, 'h': 95, 'title': 'Минимизированный сбор ПДн', 'subtitle': 'Исключены место работы/учебы\nТолько необходимые ФИО, телефон,\nпаспорт и электронное ИДС', 'status': 'secure', 'badge': 'Data Minimization'},
        {'type': 'process', 'id': '1.2', 'x': 250, 'y': 250, 'w': 220, 'h': 95, 'title': 'Аутентификация и валидация', 'subtitle': 'Kong API Gateway + WAF\nKeycloak IdP (JWT Bearer)\nПроверка согласия на обработку', 'status': 'secure', 'badge': 'OAuth2 / mTLS'},
        {'type': 'process', 'id': '1.3', 'x': 250, 'y': 400, 'w': 220, 'h': 95, 'title': 'Псевдонимизация и тегирование', 'subtitle': 'Генерация patient_uuid\nМаркировка: PII_CONFIDENTIAL\nПолитики OPA + OpenMetadata', 'status': 'secure', 'badge': 'Data Tagging Engine'},
        {'type': 'store', 'id': 'D1', 'x': 540, 'y': 110, 'w': 230, 'h': 95, 'title': 'Patient DB (PostgreSQL)', 'subtitle': 'Шифрование TDE / pgcrypto\nRow-Level Security (RLS)\nUUID связка, аудит чтения', 'status': 'secure', 'badge': 'AES-256 / УЗ-1'},
        {'type': 'store', 'id': 'D2', 'x': 540, 'y': 260, 'w': 230, 'h': 95, 'title': 'Doc Storage (MinIO S3)', 'subtitle': 'Электронные согласия и сканы\nServer-Side Encryption (SSE-KMS)\nObject Versioning & Retention', 'status': 'secure', 'badge': 'Vault KMS'},
        {'type': 'store', 'id': 'D3', 'x': 540, 'y': 410, 'w': 230, 'h': 95, 'title': 'Audit & Event Store (Kafka)', 'subtitle': 'Централизованный Audit Log\nШина сообщений Kafka mTLS\nData Lineage фиксация', 'status': 'secure', 'badge': 'Vector / OpenSearch'},
        {'type': 'security_badge', 'id': 'SEC1', 'x': 800, 'y': 180, 'w': 160, 'h': 190, 'title': 'Меры безопасности To-Be', 'subtitle': '• TLS 1.3 шифрование\n• RBAC/ABAC доступ\n• Токенизация patient_id\n• Тегирование PII\n• Автоматический аудит\n• Поддержка ст. 21 152-ФЗ\n  (удаление по запросу)'}
    ],
    'flows': [
        {'from_pt': (200, 140), 'to_pt': (250, 140), 'label': 'HTTPS TLS 1.3:\nФИО, контакты, паспорт, ИДС', 'style': 'secure'},
        {'from_pt': (200, 310), 'to_pt': (250, 290), 'label': 'Авторизованный доступ\nк АРМ (Keycloak 2FA)', 'style': 'secure'},
        {'from_pt': (360, 190), 'to_pt': (360, 250), 'label': 'Передача профиля\nчерез API Gateway', 'style': 'secure'},
        {'from_pt': (360, 345), 'to_pt': (360, 400), 'label': 'Обогащение тегами\nи генерация UUID', 'style': 'secure'},
        {'from_pt': (470, 150), 'to_pt': (540, 150), 'label': 'Запись карточки\nпациента (TDE)', 'style': 'secure'},
        {'from_pt': (470, 295), 'to_pt': (540, 295), 'label': 'Загрузка сканов\nс тегом PII_FILE', 'style': 'secure'},
        {'from_pt': (470, 450), 'to_pt': (540, 450), 'label': 'Событие: PatientCreated\n(Audit Lineage)', 'style': 'secure'}
    ]
}

# Process 2: Запись на прием
p2_as_is = {
    'width': 920, 'height': 520,
    'title': 'DFD Процесс 2 (As-Is): Запись пациента на приём к специалисту',
    'subtitle': 'Текущее состояние: открытые Excel-файлы расписаний по докторам, раскрытие врачебной тайны, коллизии блокировок',
    'elements': [
        {'type': 'entity', 'id': 'E1', 'x': 40, 'y': 100, 'w': 180, 'h': 85, 'title': 'Пациент (Patient)', 'subtitle': 'Обращение по телефону\nили лично на стойку'},
        {'type': 'entity', 'id': 'E2', 'x': 40, 'y': 250, 'w': 180, 'h': 85, 'title': 'Ресепшен (Receptionist)', 'subtitle': 'Администратор ведет запись\nв файлы расписаний'},
        {'type': 'entity', 'id': 'E3', 'x': 40, 'y': 400, 'w': 180, 'h': 85, 'title': 'Врач (Doctor)', 'subtitle': 'Медицинский специалист\n15 сотрудников'},
        {'type': 'process', 'id': '2.1', 'x': 290, 'y': 130, 'w': 220, 'h': 95, 'title': 'Проверка расписания', 'subtitle': 'Поиск свободного слота\nв открытом файле Excel\nJournal-Doctor-FIO.xlsx', 'status': 'vulnerable', 'badge': 'Коллизии файлов'},
        {'type': 'process', 'id': '2.2', 'x': 290, 'y': 290, 'w': 220, 'h': 95, 'title': 'Внесение записи на прием', 'subtitle': 'Ручной ввод ФИО, телефона,\nспециальности и причины\nвизита в ячейку таблицы', 'status': 'vulnerable', 'badge': 'Утечка врачебной тайны'},
        {'type': 'store', 'id': 'D1', 'x': 590, 'y': 200, 'w': 290, 'h': 120, 'title': 'Файловый диск: \\\\Journals\\*', 'subtitle': 'Таблицы: Journal-Doctor-FIO.xlsx\nКаждый врач и администратор имеет\nдоступ к расписанию ВСЕХ врачей клиники!\nНарушение ст. 13 323-ФЗ (врачебная тайна)', 'status': 'vulnerable', 'badge': 'Критический риск'}
    ],
    'flows': [
        {'from_pt': (220, 140), 'to_pt': (290, 160), 'label': 'Запрос записи: специальность,\nФИО, телефон, симптомы', 'style': 'vulnerable'},
        {'from_pt': (220, 275), 'to_pt': (290, 190), 'label': 'Открытие файла Excel\nдоктора через SMB', 'style': 'normal'},
        {'from_pt': (390, 225), 'to_pt': (390, 290), 'label': 'Выбор свободного\nслота времени', 'style': 'normal'},
        {'from_pt': (510, 320), 'to_pt': (590, 280), 'label': 'Сохранение файла\nJournal-Doctor-FIO.xlsx', 'style': 'vulnerable'},
        {'from_pt': (220, 430), 'to_pt': (590, 310), 'label': 'Врач открывает расписание\n(и может открыть чужие файлы!)', 'style': 'vulnerable'}
    ]
}

p2_to_be = {
    'width': 980, 'height': 560,
    'title': 'DFD Процесс 2 (To-Be): Автоматизированная запись на прием с RBAC/ABAC',
    'subtitle': 'Целевое состояние: ЛК пациента, RBAC изоляция журналов врачей, Kafka нотификации, токенизация appointments',
    'elements': [
        {'type': 'entity', 'id': 'E1', 'x': 30, 'y': 90, 'w': 170, 'h': 85, 'title': 'Пациент (Client)', 'subtitle': 'Web-портал / Мобильное App\nАвтономная запись 24/7'},
        {'type': 'entity', 'id': 'E2', 'x': 30, 'y': 240, 'w': 170, 'h': 85, 'title': 'Ресепшен (Staff)', 'subtitle': 'АРМ ресепшена\nТолько общие слоты'},
        {'type': 'entity', 'id': 'E3', 'x': 30, 'y': 390, 'w': 170, 'h': 85, 'title': 'Врач (Doctor)', 'subtitle': 'АРМ врача (RBAC/ABAC)\nВидит ТОЛЬКО своих пациентов'},
        {'type': 'process', 'id': '2.1', 'x': 250, 'y': 100, 'w': 220, 'h': 95, 'title': 'Запрос расписания (API)', 'subtitle': 'Фильтрация доступных слотов\nБез раскрытия чужих данных\nRate limiting + WAF', 'status': 'secure', 'badge': 'Data Minimization'},
        {'type': 'process', 'id': '2.2', 'x': 250, 'y': 250, 'w': 220, 'h': 95, 'title': 'Бронирование визита', 'subtitle': 'Appointment Service (OLTP)\nАтомарная транзакция в PostgreSQL\nТег: PHI_APPOINTMENT', 'status': 'secure', 'badge': 'Zero Collisions'},
        {'type': 'process', 'id': '2.3', 'x': 250, 'y': 400, 'w': 220, 'h': 95, 'title': 'Оповещения и напоминания', 'subtitle': 'Notification Service (Kafka)\nSMS/Push за 24ч до приема\nБез раскрытия диагноза', 'status': 'secure', 'badge': 'Privacy-preserving'},
        {'type': 'store', 'id': 'D1', 'x': 540, 'y': 170, 'w': 240, 'h': 95, 'title': 'Appointment DB (PostgreSQL)', 'subtitle': 'Слоты, patient_uuid, doctor_id\nABAC правила доступа (OPA)\nИсключены коллизии блокировок', 'status': 'secure', 'badge': 'TDE / RLS'},
        {'type': 'store', 'id': 'D2', 'x': 540, 'y': 340, 'w': 240, 'h': 95, 'title': 'Message Broker (Kafka mTLS)', 'subtitle': 'Топик appointments.events\nСобытия: Created, Confirmed, Cancelled\nШифрование payload + audit', 'status': 'secure', 'badge': 'Audit & Events'},
        {'type': 'security_badge', 'id': 'SEC1', 'x': 810, 'y': 190, 'w': 155, 'h': 180, 'title': 'Защитные механизмы', 'subtitle': '• Врач видит ТОЛЬКО\n  свое расписание (ABAC)\n• Пациент видит только\n  свободные временные окна\n• Нет утечки диагнозов\n• Логирование в SIEM\n• Высокая доступность'}
    ],
    'flows': [
        {'from_pt': (200, 130), 'to_pt': (250, 130), 'label': 'HTTPS TLS 1.3: Поиск врача/слота', 'style': 'secure'},
        {'from_pt': (200, 280), 'to_pt': (250, 270), 'label': 'Создание записи с ресепшена', 'style': 'secure'},
        {'from_pt': (200, 430), 'to_pt': (250, 420), 'label': 'Запрос журнала (только свой doctor_id)', 'style': 'secure'},
        {'from_pt': (360, 195), 'to_pt': (360, 250), 'label': 'Выбор интервала', 'style': 'secure'},
        {'from_pt': (470, 270), 'to_pt': (540, 230), 'label': 'Фиксация брони в БД', 'style': 'secure'},
        {'from_pt': (360, 345), 'to_pt': (360, 400), 'label': 'Инициация события', 'style': 'secure'},
        {'from_pt': (470, 420), 'to_pt': (540, 390), 'label': 'Публикация брони в Kafka', 'style': 'secure'}
    ]
}

# Process 3: Прием и ведение медкарты
p3_as_is = {
    'width': 920, 'height': 520,
    'title': 'DFD Процесс 3 (As-Is): Проведение медицинского приёма и ведение медкарты',
    'subtitle': 'Текущее состояние: файлы Word/Excel на файловом сервере, нет ЭЦП, нет версионирования, доступ открыт всей сети',
    'elements': [
        {'type': 'entity', 'id': 'E1', 'x': 40, 'y': 120, 'w': 180, 'h': 85, 'title': 'Пациент (Patient)', 'subtitle': 'Очный прием в кабинете\nОпрос, осмотр'},
        {'type': 'entity', 'id': 'E2', 'x': 40, 'y': 310, 'w': 180, 'h': 85, 'title': 'Врач (Doctor)', 'subtitle': 'Медицинский специалист\nПК в локальной сети'},
        {'type': 'process', 'id': '3.1', 'x': 290, 'y': 100, 'w': 220, 'h': 95, 'title': 'Поиск медкарты в проводнике', 'subtitle': 'Открытие сетевой папки\n\\\\Pacients\\Pacient1-FIO-BD\nЧтение Word/PDF файлов', 'status': 'vulnerable', 'badge': 'Нет аудита чтения'},
        {'type': 'process', 'id': '3.2', 'x': 290, 'y': 250, 'w': 220, 'h': 95, 'title': 'Осмотр и оформление карты', 'subtitle': 'Внесение жалоб, диагноза (МКБ),\nназначений в локальный файл Word\nБЕЗ цифровой подписи (ЭЦП)', 'status': 'vulnerable', 'badge': 'Нет юр. значимости'},
        {'type': 'process', 'id': '3.3', 'x': 290, 'y': 390, 'w': 220, 'h': 95, 'title': 'Печать заключений', 'subtitle': 'Вывод на локальный принтер\nбумажного листа с диагнозом\nи назначением лечения', 'status': 'normal', 'badge': 'Бумажный след'},
        {'type': 'store', 'id': 'D1', 'x': 590, 'y': 160, 'w': 300, 'h': 140, 'title': 'Файловый диск: Медкарты пациентов', 'subtitle': 'Каталоги \\\\Pacients\\Pacient-FIO-BD\\\nФайлы DOCX, PDF, XLSX, JPG\n• Доступен любому ПК в офисе\n• Нет неизменяемости (WORM)\n• Нет журналирования (кто читал?)\n• Нарушение 323-ФЗ и УЗ-1 (ФСТЭК № 21)', 'status': 'vulnerable', 'badge': 'Критическая уязвимость'}
    ],
    'flows': [
        {'from_pt': (220, 150), 'to_pt': (290, 150), 'label': 'Озвучивание жалоб,\nанамнез, симптомы', 'style': 'vulnerable'},
        {'from_pt': (220, 340), 'to_pt': (290, 180), 'label': 'Поиск папки пациента\nв проводнике Windows', 'style': 'normal'},
        {'from_pt': (390, 195), 'to_pt': (390, 250), 'label': 'Загрузка старых записей\nв Word без аудита', 'style': 'vulnerable'},
        {'from_pt': (510, 270), 'to_pt': (590, 230), 'label': 'Перезапись файла DOCX\nпо открытому SMB', 'style': 'vulnerable'},
        {'from_pt': (390, 345), 'to_pt': (390, 390), 'label': 'Отправка на печать', 'style': 'normal'},
        {'from_pt': (290, 430), 'to_pt': (220, 200), 'label': 'Бумажное заключение пациенту', 'style': 'normal'}
    ]
}

p3_to_be = {
    'width': 980, 'height': 560,
    'title': 'DFD Процесс 3 (To-Be): Защищенная электронная медицинская карта (ЭМК / EHR)',
    'subtitle': 'Целевое состояние: ABAC (доступ только на время визита), УКЭП врача, стандарты FHIR, S3 WORM, SIEM-аудит',
    'elements': [
        {'type': 'entity', 'id': 'E1', 'x': 30, 'y': 100, 'w': 170, 'h': 85, 'title': 'Пациент (Patient)', 'subtitle': 'Субъект ПДн\nЛичный кабинет (ЛК)'},
        {'type': 'entity', 'id': 'E2', 'x': 30, 'y': 280, 'w': 170, 'h': 85, 'title': 'Врач (Doctor)', 'subtitle': 'АРМ врача\nАппаратный токен УКЭП'},
        {'type': 'process', 'id': '3.1', 'x': 250, 'y': 95, 'w': 220, 'h': 95, 'title': 'ABAC авторизация доступа', 'subtitle': 'OPA Policy Engine:\nдоступ к медкарте ТОЛЬКО при\nналичии активной записи на прием', 'status': 'secure', 'badge': 'Strict ABAC'},
        {'type': 'process', 'id': '3.2', 'x': 250, 'y': 250, 'w': 220, 'h': 95, 'title': 'Ведение протокола (EHR)', 'subtitle': 'Структурированный формат FHIR\nТег: PHI_SPECIAL_RESTRICTED\nПодписание УКЭП врача (947н)', 'status': 'secure', 'badge': 'УКЭП / Минздрав 947н'},
        {'type': 'process', 'id': '3.3', 'x': 250, 'y': 405, 'w': 220, 'h': 95, 'title': 'Иммутабельное архивирование', 'subtitle': 'Шифрование AES-256 (TDE)\nПолитика неизменяемости (WORM)\nЗапрет скрытого редактирования', 'status': 'secure', 'badge': 'WORM / Immutability'},
        {'type': 'store', 'id': 'D1', 'x': 540, 'y': 105, 'w': 230, 'h': 95, 'title': 'EHR Clinical DB (PostgreSQL)', 'subtitle': 'Медицинские записи, диагнозы МКБ\nШифрование pgcrypto/TDE\nМаскирование для не-врачей', 'status': 'secure', 'badge': 'PostgreSQL TDE'},
        {'type': 'store', 'id': 'D2', 'x': 540, 'y': 255, 'w': 230, 'h': 95, 'title': 'Medical Docs (MinIO S3 SSE)', 'subtitle': 'Подписанные PDF/A, снимки, ЭКГ\nKMS Envelope Encryption\nObject Lock (Immutability)', 'status': 'secure', 'badge': 'SSE-KMS / WORM'},
        {'type': 'store', 'id': 'D3', 'x': 540, 'y': 405, 'w': 230, 'h': 95, 'title': 'SIEM & Audit Vault', 'subtitle': 'Полная фиксация каждого чтения!\nVector -> OpenSearch -> Wazuh\nСрок хранения логов 5 лет', 'status': 'secure', 'badge': 'Неотслеживаемость исключена'},
        {'type': 'security_badge', 'id': 'SEC1', 'x': 800, 'y': 180, 'w': 160, 'h': 195, 'title': 'Гарантии безопасности', 'subtitle': '• Врач другой специальности\n  НЕ МОЖЕТ открыть карту\n• Каждая запись подписана\n  личной УКЭП врача\n• Невозможно подделать\n  или удалить историю болезни\n• 100% аудит просмотров\n• Полное соответствие 323-ФЗ'}
    ],
    'flows': [
        {'from_pt': (200, 310), 'to_pt': (250, 160), 'label': 'Запрос ЭМК пациента (mTLS)', 'style': 'secure'},
        {'from_pt': (360, 190), 'to_pt': (360, 250), 'label': 'Разрешение OPA (ABAC OK)', 'style': 'secure'},
        {'from_pt': (470, 145), 'to_pt': (540, 145), 'label': 'Чтение медкарты (Audit Logged)', 'style': 'secure'},
        {'from_pt': (470, 290), 'to_pt': (540, 290), 'label': 'Сохранение протокола + УКЭП', 'style': 'secure'},
        {'from_pt': (360, 345), 'to_pt': (360, 405), 'label': 'Блокировка изменений', 'style': 'secure'},
        {'from_pt': (470, 445), 'to_pt': (540, 445), 'label': 'Отправка лога в SIEM', 'style': 'secure'},
        {'from_pt': (250, 120), 'to_pt': (200, 120), 'label': 'Доступ к своей карте в ЛК', 'style': 'secure'}
    ]
}

# Process 4: Лабораторные исследования
p4_as_is = {
    'width': 920, 'height': 520,
    'title': 'DFD Процесс 4 (As-Is): Направление и получение анализов из лаборатории',
    'subtitle': 'Текущее состояние: открытый Exchange e-mail, незащищенные реестры анализов, отсутствие деперсонализации биоматериала',
    'elements': [
        {'type': 'entity', 'id': 'E1', 'x': 40, 'y': 90, 'w': 180, 'h': 85, 'title': 'Пациент (Patient)', 'subtitle': 'Сдает биоматериал\nв процедурном кабинете'},
        {'type': 'entity', 'id': 'E2', 'x': 40, 'y': 240, 'w': 180, 'h': 85, 'title': 'Медсестра / Ресепшен', 'subtitle': 'Оформляет суточный реестр\nи отправляет пробирки'},
        {'type': 'entity', 'id': 'E3', 'x': 40, 'y': 390, 'w': 180, 'h': 85, 'title': 'Внешняя лаборатория', 'subtitle': 'Партнерская лаборатория\nОбмен через Exchange / файлы'},
        {'type': 'process', 'id': '4.1', 'x': 290, 'y': 130, 'w': 220, 'h': 95, 'title': 'Ведение реестра анализов', 'subtitle': 'Внесение ФИО, даты, видов\nисследований в Excel\nRegistryByDate.xlsx', 'status': 'vulnerable', 'badge': 'Нет шифрования'},
        {'type': 'process', 'id': '4.2', 'x': 290, 'y': 285, 'w': 220, 'h': 95, 'title': 'Передача реестра партнеру', 'subtitle': 'Отправка списка пациентов\nи забор пробирок курьером\nбез деперсонализации', 'status': 'vulnerable', 'badge': 'Нарушение тайны'},
        {'type': 'process', 'id': '4.3', 'x': 290, 'y': 415, 'w': 220, 'h': 95, 'title': 'Прием результатов (e-mail)', 'subtitle': 'Получение PDF/XLS по Exchange,\nручное копирование в папки\nпациентов на файловом диске', 'status': 'vulnerable', 'badge': 'Открытый e-mail'},
        {'type': 'store', 'id': 'D1', 'x': 590, 'y': 190, 'w': 300, 'h': 130, 'title': 'Файловый диск: Laboratory Registry', 'subtitle': 'Каталоги \\\\Laboratory Registry\\RegistryByDate.xlsx\n• Доступен всем сотрудникам\n• Содержит ФИО + ВИЧ, гепатиты, онкомаркеры!\n• Нарушение ст. 10 152-ФЗ и ст. 13 323-ФЗ', 'status': 'vulnerable', 'badge': 'Утечка спецкатегорий'}
    ],
    'flows': [
        {'from_pt': (220, 130), 'to_pt': (290, 150), 'label': 'Забор биоматериала (ФИО на пробирке)', 'style': 'vulnerable'},
        {'from_pt': (220, 270), 'to_pt': (290, 180), 'label': 'Ручной ввод в RegistryByDate.xlsx', 'style': 'normal'},
        {'from_pt': (510, 200), 'to_pt': (590, 230), 'label': 'Запись строки в Excel', 'style': 'vulnerable'},
        {'from_pt': (390, 225), 'to_pt': (390, 285), 'label': 'Формирование списка отправки', 'style': 'normal'},
        {'from_pt': (290, 335), 'to_pt': (220, 420), 'label': 'Отправка реестра с ФИО курьеру', 'style': 'vulnerable'},
        {'from_pt': (220, 440), 'to_pt': (290, 445), 'label': 'Результаты анализов по незашифрованному Exchange', 'style': 'vulnerable'},
        {'from_pt': (510, 450), 'to_pt': (590, 280), 'label': 'Раскладывание PDF по папкам \\\\Pacients\\', 'style': 'vulnerable'}
    ]
}

p4_to_be = {
    'width': 980, 'height': 560,
    'title': 'DFD Процесс 4 (To-Be): Защищенная интеграция с лабораторией (Lab API / mTLS)',
    'subtitle': 'Целевое состояние: деперсонализация биоматериала (barcode token), mTLS API контракты, Webhook, исключение утечек',
    'elements': [
        {'type': 'entity', 'id': 'E1', 'x': 30, 'y': 90, 'w': 170, 'h': 85, 'title': 'Пациент (Patient)', 'subtitle': 'Сдает биоматериал\nРезультаты в ЛК'},
        {'type': 'entity', 'id': 'E2', 'x': 30, 'y': 240, 'w': 170, 'h': 85, 'title': 'Процедурный кабинет', 'subtitle': 'Медсестра (АРМ)\nМаркировка пробирок'},
        {'type': 'entity', 'id': 'E3', 'x': 30, 'y': 400, 'w': 170, 'h': 85, 'title': 'Внешняя лаборатория', 'subtitle': 'Lab API Partner\nИнтеграция по стандарту'},
        {'type': 'process', 'id': '4.1', 'x': 250, 'y': 95, 'w': 220, 'h': 95, 'title': 'Деперсонализация заказа', 'subtitle': 'Генерация sample_uuid и barcode.\nЛаборатории передается ТОЛЬКО код,\nпол, возраст (без ФИО и паспорта)', 'status': 'secure', 'badge': 'Pseudonymization'},
        {'type': 'process', 'id': '4.2', 'x': 250, 'y': 250, 'w': 220, 'h': 95, 'title': 'Защищенный API Gateway', 'subtitle': 'Взаимная аутентификация mTLS\nСтрогий OpenAPI контракт\nВалидация входящей схемы', 'status': 'secure', 'badge': 'mTLS / Zero Trust'},
        {'type': 'process', 'id': '4.3', 'x': 250, 'y': 405, 'w': 220, 'h': 95, 'title': 'Реидентификация и доставка', 'subtitle': 'Сопоставление sample_uuid -> patient_uuid\nв закрытом изолированном Vault.\nТег: PHI_LAB_RESULT', 'status': 'secure', 'badge': 'Tokenization Vault'},
        {'type': 'store', 'id': 'D1', 'x': 540, 'y': 105, 'w': 230, 'h': 95, 'title': 'Token Vault (HashiCorp)', 'subtitle': 'Таблица связки: barcode <-> patient_uuid\nДоступна ТОЛЬКО Lab Service\nИзолирована от внешнего контура', 'status': 'secure', 'badge': 'Isolated Vault'},
        {'type': 'store', 'id': 'D2', 'x': 540, 'y': 255, 'w': 230, 'h': 95, 'title': 'Lab Orders DB (PostgreSQL)', 'subtitle': 'Статусы заказов, даты готовности\nШифрование TDE\nБез персональных данных', 'status': 'secure', 'badge': 'Anonymized Orders'},
        {'type': 'store', 'id': 'D3', 'x': 540, 'y': 405, 'w': 230, 'h': 95, 'title': 'Results Storage (MinIO S3)', 'subtitle': 'Зашифрованные PDF бланки\nSSE-KMS шифрование\nДоступ пациенту только к своим!', 'status': 'secure', 'badge': 'SSE-KMS / RLS'},
        {'type': 'security_badge', 'id': 'SEC1', 'x': 800, 'y': 180, 'w': 160, 'h': 195, 'title': 'Принципы защиты', 'subtitle': '• Партнер НЕ ЗНАЕТ ФИО\n  пациента (только barcode)\n• Никаких Excel реестров\n• Никаких пересылок по mail\n• Двусторонний mTLS\n• Исключен просмотр чужих\n  анализов другими клиентами'}
    ],
    'flows': [
        {'from_pt': (200, 270), 'to_pt': (250, 160), 'label': 'Создание заказа на исследование', 'style': 'secure'},
        {'from_pt': (470, 140), 'to_pt': (540, 140), 'label': 'Сохранение токена barcode', 'style': 'secure'},
        {'from_pt': (360, 190), 'to_pt': (360, 250), 'label': 'Передача деперсонализированного заказа', 'style': 'secure'},
        {'from_pt': (250, 310), 'to_pt': (200, 420), 'label': 'mTLS API: отправка barcode + анализ', 'style': 'secure'},
        {'from_pt': (200, 450), 'to_pt': (250, 440), 'label': 'mTLS Webhook: результат с barcode', 'style': 'secure'},
        {'from_pt': (360, 345), 'to_pt': (360, 405), 'label': 'Валидация подписи лаборатории', 'style': 'secure'},
        {'from_pt': (470, 440), 'to_pt': (540, 440), 'label': 'Сохранение PDF в MinIO S3', 'style': 'secure'},
        {'from_pt': (250, 110), 'to_pt': (200, 110), 'label': 'Push-уведомление в ЛК пациента', 'style': 'secure'}
    ]
}

# Process 5: Оплата и фискализация
p5_as_is = {
    'width': 920, 'height': 520,
    'title': 'DFD Процесс 5 (As-Is): Оплата медицинских услуг и фискализация',
    'subtitle': 'Текущее состояние: двойной учет (Excel + 1С), незащищенный протокол ККМ, файловая БД «1С:Бухгалтерия»',
    'elements': [
        {'type': 'entity', 'id': 'E1', 'x': 40, 'y': 100, 'w': 180, 'h': 85, 'title': 'Пациент (Patient)', 'subtitle': 'Оплата на кассе\nналичные / карта'},
        {'type': 'entity', 'id': 'E2', 'x': 40, 'y': 250, 'w': 180, 'h': 85, 'title': 'Кассир (Cashier)', 'subtitle': '3 сотрудника кассы\nДвойной учет'},
        {'type': 'entity', 'id': 'E3', 'x': 40, 'y': 400, 'w': 180, 'h': 85, 'title': 'ККМ (Кассовый аппарат)', 'subtitle': 'Контрольно-кассовая машина\nСвязь по TCP/IP OLE'},
        {'type': 'process', 'id': '5.1', 'x': 290, 'y': 110, 'w': 220, 'h': 95, 'title': 'Прием платежа на кассе', 'subtitle': 'Расчет стоимости услуг,\nприем средств, ввод в локальный\nфайл Excel кассира', 'status': 'vulnerable', 'badge': 'Двойной учет'},
        {'type': 'process', 'id': '5.2', 'x': 290, 'y': 250, 'w': 220, 'h': 95, 'title': 'Пробитие чека через ККМ', 'subtitle': 'Передача команды в ККМ по TCP/IP\nчерез устаревшую OLE-компоненту\nбез шифрования трафика', 'status': 'vulnerable', 'badge': 'Незащищенный TCP/IP'},
        {'type': 'process', 'id': '5.3', 'x': 290, 'y': 390, 'w': 220, 'h': 95, 'title': 'Проводка в «1С:Бухгалтерия»', 'subtitle': 'Ручное создание документа оплаты\nв файловой базе 1С по сети SMB\n(риск порчи базы при сбое сети)', 'status': 'vulnerable', 'badge': 'Файловый режим 1С'},
        {'type': 'store', 'id': 'D1', 'x': 590, 'y': 160, 'w': 290, 'h': 100, 'title': 'Локальный Excel кассира', 'subtitle': 'Файлы учета платежей на ПК кассиров\nНе централизованы, нет контроля доступа,\nрассинхронизация с бухгалтерией', 'status': 'vulnerable', 'badge': 'Shadow Data'},
        {'type': 'store', 'id': 'D2', 'x': 590, 'y': 340, 'w': 290, 'h': 110, 'title': '1С:Бухгалтерия (файловая БД)', 'subtitle': 'Сетевой путь: \\\\Server\\1C_Buh\\\n• Блокировки таблиц\n• Нет шифрования сетевого трафика\n• Риск повреждения при скачке питания', 'status': 'vulnerable', 'badge': 'Риск потери данных'}
    ],
    'flows': [
        {'from_pt': (220, 135), 'to_pt': (290, 140), 'label': 'Передача наличных / карты', 'style': 'normal'},
        {'from_pt': (220, 275), 'to_pt': (290, 170), 'label': 'Ввод суммы и ФИО в Excel', 'style': 'normal'},
        {'from_pt': (510, 160), 'to_pt': (590, 190), 'label': 'Сохранение кассового Excel', 'style': 'vulnerable'},
        {'from_pt': (390, 205), 'to_pt': (390, 250), 'label': 'Команда на фискализацию', 'style': 'normal'},
        {'from_pt': (290, 310), 'to_pt': (220, 420), 'label': 'TCP/IP OLE (открытый трафик)', 'style': 'vulnerable'},
        {'from_pt': (220, 440), 'to_pt': (220, 170), 'label': 'Выдача бумажного чека пациенту', 'style': 'normal'},
        {'from_pt': (390, 345), 'to_pt': (390, 390), 'label': 'Синхронизация с 1С', 'style': 'normal'},
        {'from_pt': (510, 420), 'to_pt': (590, 390), 'label': 'Запись в файловую БД 1С по SMB', 'style': 'vulnerable'}
    ]
}

p5_to_be = {
    'width': 980, 'height': 560,
    'title': 'DFD Процесс 5 (To-Be): Защищенный платежный шлюз и фискализация (PCI DSS / 54-ФЗ)',
    'subtitle': 'Целевое состояние: Payment Gateway, СБП/Эквайринг (без хранения карт), ОФД, 1С клиент-сервер по API/Kafka',
    'elements': [
        {'type': 'entity', 'id': 'E1', 'x': 30, 'y': 90, 'w': 170, 'h': 85, 'title': 'Пациент (Client)', 'subtitle': 'Оплата в App / ЛК / СБП\nили терминал на кассе'},
        {'type': 'entity', 'id': 'E2', 'x': 30, 'y': 240, 'w': 170, 'h': 85, 'title': 'Кассир / Ресепшен', 'subtitle': 'АРМ кассира (RBAC)\nФормирование счетов'},
        {'type': 'entity', 'id': 'E3', 'x': 30, 'y': 400, 'w': 170, 'h': 85, 'title': 'Банк-эквайер / ОФД', 'subtitle': 'Внешний шлюз эквайринга\nОператор фискальных данных'},
        {'type': 'process', 'id': '5.1', 'x': 250, 'y': 95, 'w': 220, 'h': 95, 'title': 'Billing & Invoicing Service', 'subtitle': 'Формирование инвойса по заказу.\nСвязка order_uuid + сумма.\nМаскирование мед. диагнозов', 'status': 'secure', 'badge': 'Data Minimization'},
        {'type': 'process', 'id': '5.2', 'x': 250, 'y': 250, 'w': 220, 'h': 95, 'title': 'Payment Gateway (PCI DSS)', 'subtitle': 'Токенизация карт в банке.\nКлиника НЕ хранит данные карт!\nTLS 1.3 + криптоподпись webhook', 'status': 'secure', 'badge': 'PCI DSS Level 1'},
        {'type': 'process', 'id': '5.3', 'x': 250, 'y': 405, 'w': 220, 'h': 95, 'title': 'Fiscal & 1C Sync Service', 'subtitle': 'Автоматическая фискализация (54-ФЗ),\nэлектронный чек по SMS/email,\nсобытие в Kafka для клиент-серверной 1С', 'status': 'secure', 'badge': '54-ФЗ / Kafka'},
        {'type': 'store', 'id': 'D1', 'x': 540, 'y': 105, 'w': 230, 'h': 95, 'title': 'Billing DB (PostgreSQL)', 'subtitle': 'Счета, транзакции, фискальные теги\nШифрование TDE\nТег: FINANCIAL_CONFIDENTIAL', 'status': 'secure', 'badge': 'TDE / RLS'},
        {'type': 'store', 'id': 'D2', 'x': 540, 'y': 255, 'w': 230, 'h': 95, 'title': 'Audit & Kafka Pipeline', 'subtitle': 'Топик billing.payments.completed\nАсинхронная доставка в бухгалтерию\nИдемпотентность транзакций', 'status': 'secure', 'badge': 'mTLS Kafka'},
        {'type': 'store', 'id': 'D3', 'x': 540, 'y': 405, 'w': 230, 'h': 95, 'title': '1С (Клиент-Сервер)', 'subtitle': 'PostgreSQL база данных 1С\nИнтеграция по REST API/Kafka\nИсключены файловые блокировки', 'status': 'secure', 'badge': 'Enterprise 1C'},
        {'type': 'security_badge', 'id': 'SEC1', 'x': 800, 'y': 180, 'w': 160, 'h': 195, 'title': 'Принципы защиты', 'subtitle': '• Данные карт НЕ попадают\n  на сервер клиники (СБП)\n• Бухгалтерия видит только код\n  услуги (без диагнозов!)\n• Исключен теневой Excel\n• Электронный чек в ОФД\n• Клиент-серверная 1С'}
    ],
    'flows': [
        {'from_pt': (200, 130), 'to_pt': (250, 130), 'label': 'Оплата: СБП / Карта / ЛК (TLS 1.3)', 'style': 'secure'},
        {'from_pt': (200, 270), 'to_pt': (250, 160), 'label': 'Формирование счета на кассе', 'style': 'secure'},
        {'from_pt': (360, 190), 'to_pt': (360, 250), 'label': 'Передача платежного токена', 'style': 'secure'},
        {'from_pt': (250, 320), 'to_pt': (200, 420), 'label': 'Проведение платежа в банке', 'style': 'secure'},
        {'from_pt': (200, 450), 'to_pt': (250, 430), 'label': 'Webhook от банка + ОФД чек', 'style': 'secure'},
        {'from_pt': (470, 150), 'to_pt': (540, 150), 'label': 'Запись чека в Billing DB', 'style': 'secure'},
        {'from_pt': (360, 345), 'to_pt': (360, 405), 'label': 'Фискализация и нотификация', 'style': 'secure'},
        {'from_pt': (470, 440), 'to_pt': (540, 310), 'label': 'Событие PaymentSuccess в Kafka', 'style': 'secure'},
        {'from_pt': (655, 350), 'to_pt': (655, 405), 'label': 'Синхронизация с 1С', 'style': 'secure'}
    ]
}

# Process 6: Аналитика и отчетность
p6_as_is = {
    'width': 920, 'height': 520,
    'title': 'DFD Процесс 6 (As-Is): Сбор аналитики, управленческая отчетность и бизнес-анализ',
    'subtitle': 'Текущее состояние: прямой сбор неанонимизированных Excel файлов на ноутбук аналитика через SMB, Jupyter Notebook',
    'elements': [
        {'type': 'entity', 'id': 'E1', 'x': 40, 'y': 100, 'w': 180, 'h': 85, 'title': 'Бизнес-аналитик (BA)', 'subtitle': 'Сотрудник IT-отдела\nРабочий ноутбук'},
        {'type': 'entity', 'id': 'E2', 'x': 40, 'y': 280, 'w': 180, 'h': 85, 'title': 'Руководство клиники', 'subtitle': 'Генеральный директор,\nГлавный врач'},
        {'type': 'process', 'id': '6.1', 'x': 290, 'y': 95, 'w': 220, 'h': 95, 'title': 'Прямое копирование файлов', 'subtitle': 'Копирование Excel баз пациентов,\nжурналов и реестров анализов\nпо SMB на личный ноутбук', 'status': 'vulnerable', 'badge': 'Shadow Analytics'},
        {'type': 'process', 'id': '6.2', 'x': 290, 'y': 240, 'w': 220, 'h': 95, 'title': 'Расчеты в Jupyter Notebook', 'subtitle': 'Запуск локальных Python скриптов\nобработки сырых данных (ФИО, суммы,\nдиагнозы) БЕЗ обезличивания', 'status': 'vulnerable', 'badge': 'Сырые ПДн в скриптах'},
        {'type': 'process', 'id': '6.3', 'x': 290, 'y': 385, 'w': 220, 'h': 95, 'title': 'Отправка отчетов по почте', 'subtitle': 'P&L, ABC-анализ в Excel\nрассылаются через незащищенный\nExchange Mail Server', 'status': 'vulnerable', 'badge': 'Почтовая утечка'},
        {'type': 'store', 'id': 'D1', 'x': 590, 'y': 120, 'w': 290, 'h': 110, 'title': 'Файловый сервер клиники', 'subtitle': 'Папки: Pacients, Journals, Registry\nСырые файлы клиники за все годы\nДоступны аналитику без ограничений', 'status': 'vulnerable', 'badge': 'Нет Data Lineage'},
        {'type': 'store', 'id': 'D2', 'x': 590, 'y': 290, 'w': 290, 'h': 110, 'title': 'Локальный диск ноутбука аналитика', 'subtitle': 'Неконтролируемая теневая копия базы\nНет шифрования диска, нет DLP контроля,\nриск выноса базы за пределы офиса', 'status': 'vulnerable', 'badge': 'Критическая утечка'}
    ],
    'flows': [
        {'from_pt': (220, 130), 'to_pt': (290, 130), 'label': 'Запуск скрипта копирования файлов', 'style': 'normal'},
        {'from_pt': (590, 160), 'to_pt': (510, 140), 'label': 'Выгрузка сырых Excel по SMB', 'style': 'vulnerable'},
        {'from_pt': (390, 190), 'to_pt': (390, 240), 'label': 'Парсинг pandas DataFrame', 'style': 'normal'},
        {'from_pt': (510, 280), 'to_pt': (590, 320), 'label': 'Кэширование CSV на диск ПК', 'style': 'vulnerable'},
        {'from_pt': (390, 335), 'to_pt': (390, 385), 'label': 'Генерация отчета P&L, ABC', 'style': 'normal'},
        {'from_pt': (290, 430), 'to_pt': (220, 330), 'label': 'Отправка отчетов руководству по почте', 'style': 'vulnerable'}
    ]
}

p6_to_be = {
    'width': 980, 'height': 560,
    'title': 'DFD Процесс 6 (To-Be): Контур обезличенной аналитики (Data Lakehouse & Privacy Gateway)',
    'subtitle': 'Целевое состояние: Privacy Gateway (k-anonymity), ClickHouse Data Lake, Apache Superset, исключение PII из аналитики',
    'elements': [
        {'type': 'entity', 'id': 'E1', 'x': 30, 'y': 90, 'w': 170, 'h': 85, 'title': 'Бизнес-аналитик (BA)', 'subtitle': 'Доступ через Web BI\nБез права скачивания сырых ПДн'},
        {'type': 'entity', 'id': 'E2', 'x': 30, 'y': 250, 'w': 170, 'h': 85, 'title': 'ML / AI инженеры', 'subtitle': 'Обучение моделей LLM/ML\nТОЛЬКО на обезличенных сетах'},
        {'type': 'entity', 'id': 'E3', 'x': 30, 'y': 405, 'w': 170, 'h': 85, 'title': 'Руководство клиники', 'subtitle': 'Дашборды в BI Superset\nМетрики в реальном времени'},
        {'type': 'process', 'id': '6.1', 'x': 250, 'y': 95, 'w': 220, 'h': 95, 'title': 'CDC & ETL Экстракция', 'subtitle': 'Debezium + Kafka Connect\nПотоковое извлечение изменений\nиз PostgreSQL (OLTP)', 'status': 'secure', 'badge': 'CDC Streaming'},
        {'type': 'process', 'id': '6.2', 'x': 250, 'y': 250, 'w': 220, 'h': 95, 'title': 'Privacy & Anonymization Engine', 'subtitle': 'Удаление прямых идентификаторов\nК-анонимизация (возрастные группы)\nДифференциальная приватность', 'status': 'secure', 'badge': 'Роскомнадзор 996'},
        {'type': 'process', 'id': '6.3', 'x': 250, 'y': 405, 'w': 220, 'h': 95, 'title': 'Витрины данных и BI', 'subtitle': 'Агрегаты в ClickHouse (OLAP)\nДашборды в Apache Superset\nТег: ANALYTICS_ANONYMIZED', 'status': 'secure', 'badge': 'Zero Raw PII'},
        {'type': 'store', 'id': 'D1', 'x': 540, 'y': 105, 'w': 230, 'h': 95, 'title': 'Operational DBs (OLTP)', 'subtitle': 'Patient, Appointment, EHR DBs\nЗакрытый производственный контур\nПрямой доступ аналитика ЗАПРЕЩЕН', 'status': 'secure', 'badge': 'Strict Isolation'},
        {'type': 'store', 'id': 'D2', 'x': 540, 'y': 255, 'w': 230, 'h': 95, 'title': 'Analytical Lake (ClickHouse)', 'subtitle': 'Колоночная СУБД для аналитики\n100% обезличенные данные!\nАгрегаты выручки, нагрузки, услуг', 'status': 'secure', 'badge': 'ClickHouse OLAP'},
        {'type': 'store', 'id': 'D3', 'x': 540, 'y': 405, 'w': 230, 'h': 95, 'title': 'Data Catalog (OpenMetadata)', 'subtitle': 'Единый каталог метаданных\nСквозной Data Lineage от OLTP к BI\nПолитики маскирования и теги', 'status': 'secure', 'badge': 'Data Lineage'},
        {'type': 'security_badge', 'id': 'SEC1', 'x': 800, 'y': 180, 'w': 160, 'h': 195, 'title': 'Принципы защиты', 'subtitle': '• Аналитик и AI физически\n  НЕ ИМЕЮТ доступа к ПДн\n• Никаких файлов на ноутбуках\n• К-анонимизация и обобщение\n• Сквозной Data Lineage\n• Готовность к 5-кратному росту\n  и обучению LLM/ML'}
    ],
    'flows': [
        {'from_pt': (540, 140), 'to_pt': (470, 140), 'label': 'CDC поток изменений (Debezium)', 'style': 'secure'},
        {'from_pt': (360, 190), 'to_pt': (360, 250), 'label': 'Потоковая передача в Privacy Engine', 'style': 'secure'},
        {'from_pt': (470, 290), 'to_pt': (540, 290), 'label': 'Загрузка обезличенных данных', 'style': 'secure'},
        {'from_pt': (360, 345), 'to_pt': (360, 405), 'label': 'Построение витрин отчетности', 'style': 'secure'},
        {'from_pt': (470, 440), 'to_pt': (540, 440), 'label': 'Регистрация связей в Data Lineage', 'style': 'secure'},
        {'from_pt': (200, 130), 'to_pt': (250, 430), 'label': 'Аналитик открывает BI Superset (Web)', 'style': 'secure'},
        {'from_pt': (200, 280), 'to_pt': (540, 310), 'label': 'ML обучение на ClickHouse витринах', 'style': 'secure'},
        {'from_pt': (250, 460), 'to_pt': (200, 460), 'label': 'Дашборды руководству в браузере', 'style': 'secure'}
    ]
}

all_diagrams = [
    ('dfd-p1-registration-as-is', p1_as_is),
    ('dfd-p1-registration-to-be', p1_to_be),
    ('dfd-p2-scheduling-as-is', p2_as_is),
    ('dfd-p2-scheduling-to-be', p2_to_be),
    ('dfd-p3-consultation-as-is', p3_as_is),
    ('dfd-p3-consultation-to-be', p3_to_be),
    ('dfd-p4-lab-as-is', p4_as_is),
    ('dfd-p4-lab-to-be', p4_to_be),
    ('dfd-p5-payment-as-is', p5_as_is),
    ('dfd-p5-payment-to-be', p5_to_be),
    ('dfd-p6-analytics-as-is', p6_as_is),
    ('dfd-p6-analytics-to-be', p6_to_be)
]

for name, diag in all_diagrams:
    svg_content = create_svg(
        diag['width'], diag['height'],
        diag['title'], diag['subtitle'],
        diag['elements'], diag['flows']
    )
    svg_path = os.path.join(DIAGRAMS_DIR, f"{name}.svg")
    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print(f"Generated: {svg_path}")

print(f"Successfully generated all {len(all_diagrams)} SVG diagrams.")
