#!/usr/bin/env python3
"""Generate the classifier C2 view using the common C4 layout/export helpers."""
import importlib.util
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('c4_export', BASE.parent/'Task2/generate_diagrams.py')
c4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c4)


def model():
    n = c4.node
    internal = [
        n('receiver', 'Приём пакетов', 'Container', 'Источник, цель, формат и размер', 'Java API / TLS'),
        n('staging', 'Q0: приём и карантин', 'Container', 'incoming / quarantine;\nне доступен BI или ML', 'S3 / отдельный ключ'),
        n('coordinator', 'Координатор', 'Container', 'Задания, лимиты, lease и повторы', 'Java'),
        n('registry', 'Реестр заданий и схем', 'Container', 'Манифесты, fingerprints,\nрешения, версии и состояния', 'PostgreSQL'),
        n('classifier', 'Анализаторы', 'Container', 'Структура + содержимое + контекст;\nUNKNOWN → карантин', 'Python / пул работников'),
        n('transformer', 'Преобразователи / валидаторы', 'Container', 'Минимизация, псевдонимизация;\nпроверка выхода по политике', 'Python / отдельный пул'),
        n('review', 'Интерфейс проверки', 'Container', 'Решение владельца по спорному\nнабору / новой структуре', 'Web'),
        n('publisher', 'Публикатор', 'Container', 'Проверка манифеста;\nактивация полной версии', 'Java')]
    internal.append(n('access', 'Сервис выдачи', 'Container', 'Цель, права, PUBLISHED-манифест;\nодна версия для всего чтения', 'Java API / TLS'))
    outside = [
        n('files', 'Файловый архив', 'Software System', 'Excel / CSV / зарегистрированные сканы'),
        n('exports', 'Операционная платформа', 'Software System', 'Разрешённые пакетные выгрузки'),
        n('operator', 'Владелец / оператор проверки', 'Person', 'Уполномоченная проверка карантина'),
        n('iam', 'Идентификация платформы', 'Software System', 'Вход и роли / Keycloak'),
        n('policy', 'Политики платформы', 'Software System', 'Версия правил доступа / OPA'),
        n('keys', 'KMS платформы', 'Software System', 'Ключи зон и сервисные секреты'),
        n('catalog', 'Каталог метаданных', 'Software System', 'Классы, владельцы и происхождение'),
        n('audit', 'Аудит платформы', 'Software System', 'Решения, доступ и оповещения'),
        n('lake', 'Озеро платформы', 'Software System', 'L1: конфиденциальная область\nL2: проверенные наборы / S3'),
        n('warehouse', 'Витрины платформы', 'Software System', 'L3: утверждённые агрегаты\nClickHouse / закрытая промежуточная версия'),
        n('bi', 'BI / ML платформы', 'Software System', 'Только допущенная версия и цель')]
    nodes = dict(internal + outside)
    styles = {k: 'container' for k, _ in internal}
    styles.update({k: 'system' for k, _ in outside})
    styles['operator'] = 'person'
    styles.update({k:'analytics' for k in ['classifier','transformer','publisher']})
    styles['staging'] = 'security'
    edges = [
        ('files','receiver','TLS / пакет и версия'),
        ('exports','receiver','TLS / цель и контракт'),
        ('receiver','staging','TLS / закрытый оригинал'),
        ('receiver','registry','TLS / манифест'),
        ('coordinator','registry','TLS / состояния и версии'),
        ('coordinator','classifier','Задание / версия правил'),
        ('classifier','staging','TLS / читает закрытый источник'),
        ('classifier','registry','TLS / теги, схема, решение'),
        ('classifier','catalog','Классы / версия контракта','control'),
        ('coordinator','transformer','Задание после классификации'),
        ('transformer','staging','TLS / источник и закрытый результат'),
        ('transformer','registry','TLS / контроль качества'),
        ('coordinator','publisher','Только VALIDATED'),
        ('publisher','registry','TLS / манифест и состояние'),
        ('publisher','staging','TLS / проверенная версия'),
        ('publisher','lake','TLS / L1 либо L2 по политике'),
        ('publisher','warehouse','TLS / L3, затем активация'),
        ('operator','review','Решение с основанием'),
        ('review','registry','TLS / решение и новая версия'),
        ('review','staging','TLS / ограниченная проверка'),
        ('review','iam','Вход / роль','control'),
        ('coordinator','policy','Утверждённый пакет правил','control'),
        ('publisher','keys','TLS / ключи зон','control'),
        ('publisher','audit','Решение до активации','control'),
        ('bi','access','TLS / разрешённый запрос'),
        ('access','registry','TLS / опубликованный манифест'),
        ('access','lake','TLS / допущенная версия L1 либо L2'),
        ('access','warehouse','TLS / версия L3'),
        ('access','iam','Вход / область доступа','control'),
        ('access','audit','Чтение опубликованного набора','control')]
    return 'C4 / C2 — движок пакетной классификации', nodes, styles, edges, [k for k, _ in internal], 'LR'


def main():
    target = BASE/'diagrams'
    target.mkdir(exist_ok=True)
    data = model()
    source = c4.dot_source(data).replace('Медицинская платформа — граница системы',
                                       'Движок классификации — граница подсистемы')
    source = source.replace('пунктирная рамка — граница платформы', 'пунктирная рамка — граница движка')
    svg = subprocess.run(['dot','-Tsvg'], input=source, text=True, capture_output=True, check=True).stdout
    (target/'classification-engine-c2.svg').write_text(svg,encoding='utf-8')
    layout = json.loads(subprocess.run(['dot','-Tjson'], input=source, text=True, capture_output=True, check=True).stdout)
    mxfile = ET.Element('mxfile',host='app.diagrams.net',version='24.7.5')
    c4.drawio_page(mxfile,data,layout,'classification-engine')
    ET.indent(mxfile)
    ET.ElementTree(mxfile).write(BASE/'classification-engine.drawio',encoding='utf-8',xml_declaration=True)


if __name__ == '__main__':
    main()
