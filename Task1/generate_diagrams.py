#!/usr/bin/env python3
"""Build DFD SVGs, editable draw.io pages and their flow register from one model.

Requires Python 3 and Graphviz. Run from any directory; outputs are beside this file.
Only synthetic descriptions are used. No access to patient files or network.
"""
import argparse
import html
import json
from pathlib import Path
import subprocess
import tempfile
import textwrap
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
STORES = {
    'D1': 'Пациенты / Excel', 'D2': 'Документы и карты / JPG, PDF, Excel',
    'D3': 'Журналы записи / Excel', 'D4': 'База 1С:Бухгалтерия',
    'D5': 'Реестры анализов / Excel', 'D6': 'Учёт платежей / Excel',
    'D7': 'База 1С:Торговля и склад', 'D8': 'Почтовые ящики / Exchange',
    'D9': 'Рабочая область аналитика [Д]',
}


def entity(i, label, outside=False):
    return (i, 'entity', label, outside)


def process(i, label, controls):
    return (i, 'process', f'{i}. {label}', controls)


def store(i):
    return (i, 'store', f'{i}. {STORES[i]}', 'K1,K2,K4,K6,K8,K9')


def flow(i, a, b, label, status, detail, controls):
    return (i, a, b, label, status, detail, controls)


MODELS = [
    {
        'slug': '01-registration', 'title': 'Регистрация, запись и договор',
        'context': 'Ресепшен вручную ведёт список пациентов, журналы и договоры. Передача контактных данных от пациента и чтение существующих записей логически восстановлены.',
        'boundary': 'F1.1, F1.7 и F1.10 пересекают границу пациент ↔ компания. Канал ввода и выдачи не указан; для очного обмена нужны проверка личности и защита бумажного экземпляра, для электронного — K4/K5.',
        'nodes': [entity('patient', 'Пациент', True),
                  process('P1.1', 'Ресепшен: принять и уточнить анкету', 'K1,K2,K3,K6,K8'),
                  process('P1.2', 'Ресепшен: оформить запись', 'K1,K3,K6'),
                  process('P1.3', 'Ресепшен: оформить договор', 'K1,K2,K3,K6,K8'),
                  store('D1'), store('D2'), store('D3')],
        'flows': [
            flow('F1.1', 'patient', 'P1.1', 'Анкета и контакты', 'Л', 'Ф. И. О., дата рождения, телефон, email; расширенные поля только при обоснованной цели.', 'K2,K3,K8'),
            flow('F1.2', 'D1', 'P1.1', 'Карточка пациента', 'Л', 'Чтение существующих сведений для поиска и уточнения пациента.', 'K1,K4,K6'),
            flow('F1.3', 'P1.1', 'D1', 'Сведения пациента', 'П', 'Ручная регистрация/уточнение списка пациентов в Excel на общем диске.', 'K2,K3,K4,K6'),
            flow('F1.4', 'P1.1', 'P1.2', 'Пациент и контакт', 'Л', 'Данные для выбора специалиста и записи; диагноз и расширенная анкета не нужны.', 'K1,K3'),
            flow('F1.5', 'D3', 'P1.2', 'Расписание и записи', 'Л', 'Чтение журнала специалиста для выбора времени.', 'K1,K4,K6'),
            flow('F1.6', 'P1.2', 'D3', 'Запись на приём', 'П', 'Пациент, специалист, время приёма и рабочий статус записи.', 'K2,K3,K4,K6'),
            flow('F1.7', 'P1.2', 'patient', 'Сведения о записи', 'Л', 'Выдача пациенту сведений о его записи; чужие записи исключаются.', 'K3,K4,K5,K7'),
            flow('F1.8', 'P1.1', 'P1.3', 'Реквизиты договора', 'Л', 'Необходимые реквизиты пациента для клиентского договора.', 'K1,K3'),
            flow('F1.9', 'P1.3', 'D2', 'Договор / файл', 'П', 'Исходная схема показывает регистрацию файла пациента; договор сохраняется как логическая часть описанного процесса.', 'K2,K3,K4,K6,K8'),
            flow('F1.10', 'P1.3', 'patient', 'Экземпляр договора', 'Л', 'Выдача собственного документа после проверки получателя.', 'K4,K5,K7'),
            flow('F1.11', 'D2', 'P1.3', 'Существующий договор', 'Л', 'Чтение для проверки, уточнения или выдачи копии.', 'K1,K4,K6'),
        ],
    },
    {
        'slug': '02-care', 'title': 'Медицинский приём и карта',
        'context': 'Врач просматривает и редактирует свой журнал; карты хранятся в файлах. Чтение карты, оформление заключения и выдача результата моделируют работу с указанными медицинскими данными.',
        'boundary': 'F2.1 и F2.7 пересекают границу пациент ↔ компания. Права врача уточняются назначением на пациента; журнал и карта имеют разный состав разрешённых сведений.',
        'nodes': [entity('patient', 'Пациент', True), entity('doctor', 'Медицинский специалист'),
                  process('P2.1', 'Врач: просмотреть и уточнить журнал', 'K1,K3,K6'),
                  process('P2.2', 'Врач: провести приём и оформить карту', 'K1,K2,K3,K6,K8'),
                  store('D2'), store('D3')],
        'flows': [
            flow('F2.1', 'patient', 'P2.2', 'Жалобы и анамнез', 'Л', 'Сведения о здоровье, в том числе хронических заболеваниях из расширенной анкеты.', 'K2,K3,K8'),
            flow('F2.2', 'doctor', 'P2.1', 'Изменения журнала', 'П', 'Врач просматривает и редактирует собственный журнал, как показано в исходной схеме.', 'K1,K6'),
            flow('F2.3', 'D3', 'P2.1', 'Записи к врачу', 'П', 'Чтение записей из журнала специалиста.', 'K1,K4,K6'),
            flow('F2.4', 'P2.1', 'D3', 'Статус записи', 'П', 'Редактирование журнала специалистом; точный набор статусов не определён.', 'K1,K3,K4,K6'),
            flow('F2.5', 'P2.1', 'P2.2', 'Пациент и приём', 'Л', 'Связывание записи с пациентом и его картой.', 'K1,K3,K7'),
            flow('F2.6', 'D2', 'P2.2', 'Карта и результаты', 'Л', 'Чтение медицинских документов разрешённого пациента.', 'K1,K4,K6'),
            flow('F2.7', 'P2.2', 'patient', 'Заключение', 'Л', 'Выдача собственного заключения; канал и правила выдачи требуют уточнения.', 'K3,K4,K5,K7'),
            flow('F2.8', 'P2.2', 'D2', 'Карта и заключение', 'Л', 'Сохранение результатов приёма в файлах общего диска.', 'K2,K3,K4,K6,K8'),
            flow('F2.9', 'doctor', 'P2.2', 'Результаты осмотра', 'Л', 'Врач вводит клинические сведения и оформляет медицинский документ.', 'K1,K2,K6'),
        ],
    },
    {
        'slug': '03-laboratory', 'title': 'Направления и результаты анализов',
        'context': 'Лаборатория и ежедневные реестры анализов присутствуют в исходной архитектуре, но стрелок к лаборатории нет. Обмен направлениями/результатами показан как допущение; действующий API не предполагается.',
        'boundary': 'F3.1 и F3.2 пересекают границу компания ↔ лаборатория; F3.7 — компания ↔ пациент. Ответственного за приём результатов, формат и канал нужно подтвердить. ККМ и бухгалтерия не должны получать клинические результаты.',
        'nodes': [entity('lab', 'Лаборатория [Д: канал]', True), entity('patient', 'Пациент', True),
                  entity('doctor', 'Медицинский специалист'),
                  process('P3.1', 'Оформить направление', 'K1,K2,K3,K6,K7'),
                  process('P3.2', 'Принять и проверить результат', 'K1,K2,K3,K6,K7'),
                  process('P3.3', 'Проверить и выдать результат', 'K1,K5,K6,K7'),
                  store('D2'), store('D5')],
        'flows': [
            flow('F3.1', 'P3.1', 'lab', 'Направление', 'Д', 'ID направления, необходимый вид анализа и минимальные сведения пациента; канал неизвестен.', 'K3,K4,K5,K7'),
            flow('F3.2', 'lab', 'P3.2', 'Результат анализа', 'Д', 'Проверить источник, ID направления и пациента, формат и целостность результата.', 'K2,K4,K7'),
            flow('F3.3', 'P3.2', 'D5', 'Запись реестра', 'Л', 'Учёт принятого результата в ежедневном Excel-реестре анализов.', 'K2,K3,K4,K6'),
            flow('F3.4', 'D5', 'P3.3', 'Результат и связь', 'Л', 'Чтение реестра для проверки принадлежности результата.', 'K1,K4,K6,K7'),
            flow('F3.5', 'P3.2', 'D2', 'Документ результата', 'Л', 'Сохранение проверенного результата в документах соответствующего пациента.', 'K2,K3,K4,K6,K8'),
            flow('F3.6', 'D2', 'P3.3', 'Документ пациента', 'Л', 'Чтение собственного результата для выдачи.', 'K1,K4,K6'),
            flow('F3.7', 'P3.3', 'patient', 'Собственный результат', 'Л', 'Получатель идентифицирован; выдаётся только разрешённый документ.', 'K3,K4,K5,K7'),
            flow('F3.8', 'doctor', 'P3.1', 'Назначение анализа', 'Л', 'Вид исследования и связь с пациентом, без полной карты.', 'K1,K3,K7'),
            flow('F3.9', 'D2', 'P3.1', 'Необходимые сведения', 'Л', 'Чтение разрешённых реквизитов для направления.', 'K1,K3,K4,K6'),
            flow('F3.10', 'P3.3', 'doctor', 'Результат для лечения', 'Л', 'Врач получает результат только для разрешённого пациента.', 'K1,K3,K7'),
        ],
    },
    {
        'slug': '04-payments', 'title': 'Оплата и бухгалтерская сверка',
        'context': 'Кассиры принимают платежи и ведут двойной учёт в Excel и 1С. ККМ связаны с 1С через TCP/IP и компоненту OLE; бухгалтерия занимается процессингом платежей. Полные данные банковской карты в материалах не указаны.',
        'boundary': 'F4.1 и F4.8 пересекают границу пациент ↔ компания. F4.3 — внутренний технический обмен ККМ/1С; защищённость фактического протокола неизвестна. Чек моделируется как выход операции приёма оплаты.',
        'nodes': [entity('patient', 'Пациент', True), entity('cashier', 'Кассир'), entity('accountant', 'Бухгалтер'),
                  process('P4.1', 'Кассир / ККМ: принять оплату', 'K1,K3,K6'),
                  process('P4.2', '1С: учесть денежные средства', 'K1,K2,K3,K6'),
                  process('P4.3', 'Бухгалтер: сверить платежи', 'K1,K3,K6'),
                  store('D4'), store('D6')],
        'flows': [
            flow('F4.1', 'patient', 'P4.1', 'Оплата и реквизиты', 'П', 'Сведения о платеже за медицинские услуги; реквизиты эквайринга не добавлены.', 'K3,K7'),
            flow('F4.2', 'cashier', 'P4.1', 'Сумма и услуга', 'П', 'Оформление оплаты кассиром через ККМ.', 'K1,K3,K6'),
            flow('F4.3', 'P4.1', 'P4.2', 'Денежные средства\nTCP/IP + OLE', 'П', 'Информация о принятии денежных средств поступает в 1С.', 'K3,K4,K6'),
            flow('F4.4', 'P4.2', 'D4', 'Учётная запись оплаты', 'П', 'Сохранение платежа в файловой базе бухгалтерской системы.', 'K2,K4,K6'),
            flow('F4.5', 'P4.1', 'D6', 'Дубль платежа', 'П', 'Кассир ведёт вторую запись в Excel. Предлагается сохранять непрозрачный ID и сумму без диагноза.', 'K2,K3,K4,K6'),
            flow('F4.6', 'D4', 'P4.3', 'Платежи 1С', 'Л', 'Чтение бухгалтерских записей для обработки и сверки.', 'K1,K4,K6'),
            flow('F4.7', 'D6', 'P4.3', 'Платежи Excel', 'Л', 'Чтение второго источника; сверка ID, суммы, даты и чека.', 'K1,K3,K4,K6'),
            flow('F4.8', 'P4.1', 'patient', 'Чек / подтверждение', 'Л', 'Выдача документа об оплате с обязательными реквизитами, без лишней клинической информации.', 'K3,K4,K5,K7'),
            flow('F4.9', 'P4.3', 'D4', 'Уточнение и сверка', 'Л', 'Результаты обработки платежей; исправления с автором и причиной.', 'K1,K4,K6'),
            flow('F4.10', 'accountant', 'P4.3', 'Решение по расхождению', 'Л', 'Бухгалтер подтверждает результат сверки или исправление.', 'K1,K6'),
            flow('F4.11', 'D4', 'P4.2', 'Существующий платёж', 'Л', 'Проверка повторного учёта и ранее записанного статуса.', 'K1,K4,K6'),
        ],
    },
    {
        'slug': '05-payroll', 'title': 'Кадры, зарплата и налоговая отчётность',
        'context': '1С используется для кадрового учёта, зарплаты и подготовки налоговых документов. Конкретные поля кадровых документов и каналы банка/налоговой не описаны; передача наружу — допущение.',
        'boundary': 'F5.5 и F5.8 пересекают границу компания ↔ внешний получатель и требуют подтверждения. Сотрудник находится внутри компании, но бухгалтерские полномочия отделяются от кадровых.',
        'nodes': [entity('employee', 'Сотрудник'), entity('accountant', 'Уполномоченный бухгалтер'),
                  entity('bank', 'Банк [Д]', True), entity('tax', 'Налоговый орган [Д]', True),
                  process('P5.1', 'Бухгалтер: вести кадровый учёт', 'K1,K2,K3,K6,K8'),
                  process('P5.2', '1С: рассчитать зарплату', 'K1,K3,K6'),
                  process('P5.3', '1С: подготовить отчётность', 'K1,K3,K6,K8'), store('D4')],
        'flows': [
            flow('F5.1', 'employee', 'P5.1', 'Кадровые сведения', 'Л', 'Состав документов не определён; не следует считать паспорт/СНИЛС подтверждёнными полями.', 'K2,K3,K8'),
            flow('F5.2', 'P5.1', 'D4', 'Кадровая запись', 'П', 'Кадровый учёт в 1С:Бухгалтерия предприятия.', 'K1,K2,K4,K6,K8'),
            flow('F5.3', 'D4', 'P5.2', 'Данные для начисления', 'Л', 'Разрешённые кадровые данные, необходимые для расчёта.', 'K1,K3,K4,K6'),
            flow('F5.4', 'P5.2', 'D4', 'Начисление зарплаты', 'П', 'Начисление зарплаты учитывается в 1С.', 'K2,K4,K6,K8'),
            flow('F5.5', 'P5.2', 'bank', 'Платёжные сведения', 'Д', 'При безналичной выплате: только необходимые реквизиты и сумма; канал неизвестен.', 'K3,K4,K5'),
            flow('F5.6', 'D4', 'P5.3', 'Данные для отчётности', 'Л', 'Чтение бухгалтерских и кадровых сведений для налоговых документов.', 'K1,K3,K4,K6'),
            flow('F5.7', 'P5.3', 'D4', 'Налоговые документы', 'П', 'Подготовка налоговой документации в бухгалтерской системе; место конкретных выгрузок требует уточнения.', 'K2,K4,K6,K8'),
            flow('F5.8', 'P5.3', 'tax', 'Регламентированная отчётность', 'Д', 'Отправка уполномоченному органу в разрешённом формате; фактическая реализация не описана.', 'K3,K4,K5'),
            flow('F5.9', 'accountant', 'P5.1', 'Кадровые изменения', 'Л', 'Уполномоченный сотрудник вводит и проверяет сведения.', 'K1,K6'),
            flow('F5.10', 'P5.2', 'employee', 'Сведения о начислении', 'Л', 'Представление сотруднику его собственных начислений; способ выдачи нужно уточнить.', 'K3,K4,K5,K7'),
            flow('F5.11', 'D4', 'P5.1', 'Существующие сведения', 'Л', 'Чтение кадровой записи при уточнении и проверке.', 'K1,K4,K6'),
        ],
    },
    {
        'slug': '06-stock', 'title': 'Склад и закупки',
        'context': 'Склад учитывает товарно-материальные ценности и закупки. Обе системы 1С обмениваются данными через OLE по исходной схеме. Состав обмена и канал поставщика требуют уточнения.',
        'boundary': 'F6.1 и F6.2 пересекают границу компания ↔ поставщик. F6.5 и F6.6 — внутренний обмен систем 1С. В него не должны попадать карты, анализы и зарплатные сведения.',
        'nodes': [entity('supplier', 'Поставщик [Д]', True), entity('warehouse', 'Сотрудник склада'),
                  process('P6.1', 'Склад / 1С: учесть закупку и ТМЦ', 'K1,K2,K3,K6'),
                  process('P6.2', '1С: согласовать бухгалтерский учёт', 'K1,K3,K6'),
                  store('D7'), store('D4')],
        'flows': [
            flow('F6.1', 'supplier', 'P6.1', 'Документы поставки', 'Д', 'Реквизиты поставки, цены и возможные контакты; наличие ПДн контактных лиц не подтверждено.', 'K2,K3,K4'),
            flow('F6.2', 'P6.1', 'supplier', 'Заказ закупки', 'Д', 'Номенклатура и количество; канал не указан, данные пациентов не нужны.', 'K3,K4,K5'),
            flow('F6.3', 'P6.1', 'D7', 'Остатки и закупки', 'П', 'Запись учёта ТМЦ в файловой системе 1С:Торговля и склад.', 'K2,K4,K6'),
            flow('F6.4', 'D7', 'P6.1', 'Остатки и документы', 'Л', 'Чтение складского учёта для закупки и движения ТМЦ.', 'K1,K4,K6'),
            flow('F6.5', 'P6.1', 'P6.2', 'Документы ТМЦ / OLE', 'П', 'Интеграция 1С подтверждена; конкретные поля обмена моделируются и должны быть согласованы.', 'K1,K3,K4,K6'),
            flow('F6.6', 'P6.2', 'P6.1', 'Сведения учёта / OLE', 'П', 'Обратный внутриплатформенный обмен показан в исходной схеме; состав неизвестен.', 'K1,K3,K4,K6'),
            flow('F6.7', 'P6.2', 'D4', 'Бухгалтерская запись', 'Л', 'Учёт закупки в бухгалтерской базе.', 'K2,K4,K6'),
            flow('F6.8', 'D4', 'P6.2', 'Учёт закупок', 'Л', 'Чтение только разрешённых складских/бухгалтерских документов.', 'K1,K3,K4,K6'),
            flow('F6.9', 'warehouse', 'P6.1', 'Движение ТМЦ', 'П', 'Сотрудник склада вводит данные движения и закупок.', 'K1,K3,K6'),
        ],
    },
    {
        'slug': '07-analytics', 'title': 'Аналитические отчёты по Excel',
        'context': 'Бизнес-аналитик умеет строить отчёт о прибыли и убытках (P&L) и отчёт о значимости товарных групп (ABC-анализ) из Excel с помощью Python/Jupyter. Источники конкретных отчётов и локальные выгрузки не описаны: показаны как допущения, а не существующее озеро данных.',
        'boundary': 'D1/D6/D7 здесь читаются; их записи показаны в процессах 1/4/6. Все потоки внутри компании; передача аналитику пересекает границу полномочий между операционной обработкой и аналитической целью. Передачу исходных данных внешним сервисам ИИ эта модель не разрешает.',
        'nodes': [entity('analyst', 'Бизнес-аналитик'), entity('management', 'Руководство'),
                  process('P7.1', 'Подготовить аналитическую выборку', 'K1,K2,K3,K5,K6,K7'),
                  process('P7.2', 'Python/Jupyter: построить отчёт', 'K1,K2,K3,K6,K7'),
                  store('D1'), store('D6'), store('D7'), store('D9')],
        'flows': [
            flow('F7.1', 'D1', 'P7.1', 'Сведения пациентов', 'Д', 'Возможный источник аналитики; для одобренной цели передавать обезличенную производную, не Ф. И. О./контакты.', 'K1,K3,K4,K6,K7'),
            flow('F7.2', 'D6', 'P7.1', 'Платежи Excel', 'Д', 'Возможная финансовая выборка; убрать идентификацию пациента и редкие сочетания.', 'K1,K3,K4,K6,K7'),
            flow('F7.3', 'D7', 'P7.1', 'Складская выгрузка', 'Д', 'Возможная выгрузка для ABC-анализа; не предоставлять полную файловую базу 1С.', 'K1,K3,K4,K5,K6'),
            flow('F7.4', 'P7.1', 'D9', 'Выборка', 'Д', 'Контролируемая рабочая копия; наследование меток и происхождения.', 'K2,K4,K6,K7,K8'),
            flow('F7.5', 'D9', 'P7.2', 'Рабочий набор', 'Д', 'Чтение разрешённой выборки; токенизированные данные остаются защищаемыми.', 'K1,K4,K6,K7'),
            flow('F7.6', 'P7.2', 'management', 'Отчёт / агрегаты', 'Л', 'Предлагается выдавать агрегированные отчёты без персональных значений и малых групп.', 'K3,K4,K5,K7'),
            flow('F7.7', 'analyst', 'P7.2', 'Параметры и расчёты', 'Л', 'Аналитик задаёт Python-расчёт и настройки отчёта по описанной компетенции.', 'K1,K3,K6'),
            flow('F7.8', 'P7.2', 'D9', 'Расчёты и отчёт', 'Д', 'Сохранение производных артефактов с метками источников до отдельного подтверждения обезличивания.', 'K2,K4,K6,K8'),
        ],
    },
    {
        'slug': '08-mail', 'title': 'Внутренний обмен через почту',
        'context': 'Outlook и Exchange есть в компании. Передача конфиденциальных вложений не подтверждена; схема показывает возможный канал утечки для инвентаризации и соответствующие правила защиты.',
        'boundary': 'Сотрудники в одном домене могут иметь разные полномочия: F8.1 и F8.5 пересекают эту границу. Exchange в исходной схеме служит внутренней почтой; внешняя переписка не принимается за установленный факт.',
        'nodes': [entity('sender', 'Сотрудник-отправитель'), entity('recipient', 'Сотрудник-получатель'),
                  process('P8.1', 'Outlook: подготовить письмо', 'K1,K2,K3,K5,K6'),
                  process('P8.2', 'Exchange: доставить письмо', 'K1,K5,K6'),
                  process('P8.3', 'Outlook: открыть письмо', 'K1,K5,K6'), store('D8')],
        'flows': [
            flow('F8.1', 'sender', 'P8.1', 'Текст / вложение', 'Д', 'При наличии ПДн/медицинских сведений назначить метки; предпочитать ссылку с проверкой прав вместо копии.', 'K2,K3,K5'),
            flow('F8.2', 'P8.1', 'P8.2', 'Письмо и адресат', 'Д', 'Проверить полномочия получателя, запрет лишних полей и медицинских тем письма.', 'K3,K4,K5'),
            flow('F8.3', 'P8.2', 'D8', 'Сообщение', 'Д', 'Сохранение сообщения и разрешённых вложений в почтовых ящиках.', 'K2,K4,K6,K8'),
            flow('F8.4', 'D8', 'P8.3', 'Сообщение ящика', 'Д', 'Чтение сообщения разрешённым получателем, учёт доступа.', 'K1,K4,K6'),
            flow('F8.5', 'P8.3', 'recipient', 'Текст / ссылка', 'Д', 'Получение письма не расширяет права на документ по ссылке.', 'K1,K3,K5'),
            flow('F8.6', 'recipient', 'P8.3', 'Запрос сообщения', 'Л', 'Получатель открывает Outlook; состав фактической почты требует обследования.', 'K1,K6'),
        ],
    },
]


def node_label(node, protected):
    i, kind, title, extra = node
    label = '\n'.join(textwrap.wrap(title, width=27, break_long_words=False, break_on_hyphens=False))
    if protected and kind != 'entity':
        label += '\n' + extra
    return label


def dot_source(model, protected):
    variant = 'Меры защиты — предложения' if protected else 'Текущее состояние — модель As-Is'
    title = f"{model['title']}\n{variant}\nОвал: операция · Прямоугольник: участник · Две линии: хранилище\n[Д] и пунктир: допущение · П/Л/Д: статус в реестре · K1–K9: меры в data-protection.md"
    lines = ['digraph DFD {',
             'graph [rankdir=TB, bgcolor="white", fontname="DejaVu Sans", fontsize=16, labelloc=t, pad=0.3, nodesep=0.45, ranksep=0.65, splines=polyline];',
             'node [fontname="DejaVu Sans", fontsize=13, margin="0.18,0.13"];',
             'edge [fontname="DejaVu Sans", fontsize=11, arrowsize=0.75];',
             f'label={json.dumps(title, ensure_ascii=False)};']
    declarations = []
    for n in model['nodes']:
        i, kind, text, extra = n
        label = node_label(n, protected)
        if kind == 'store':
            content = '<BR/>'.join(html.escape(x) for x in label.split('\n'))
            attrs = f'shape=plain, label=<<TABLE BORDER="1" SIDES="TB" CELLBORDER="0" CELLPADDING="8"><TR><TD>{content}</TD></TR></TABLE>>'
        else:
            shape = 'ellipse' if kind == 'process' else 'box'
            color = ('#e8f5ee' if protected else '#e7f0fb') if kind == 'process' else '#f1f3f5'
            attrs = f'shape={shape}, style=filled, fillcolor="{color}", label={json.dumps(label, ensure_ascii=False)}'
        decl = f'"{i}" [{attrs}];'
        if kind == 'entity' and extra:
            lines.append(decl)
        else:
            declarations.append(decl)
    lines += ['subgraph cluster_company {', 'label="Управляемый контур компании (не отдельные серверы)"; fontsize=12; color="#94a3b8"; style=dashed;']
    lines += declarations + ['}']
    for i, a, b, label, status, detail, controls in model['flows']:
        label = f'{i}: ' + '\n'.join(textwrap.wrap(label, width=29, break_long_words=False, break_on_hyphens=False)) + (' [Д]' if status == 'Д' else '')
        if protected:
            label += '\n' + controls
        attrs = f'label={json.dumps(label, ensure_ascii=False)}, style={"dashed" if status == "Д" else "solid"}'
        if protected:
            attrs += ', fontcolor="#166534"'
        lines.append(f'"{a}" -> "{b}" [{attrs}];')
    return '\n'.join(lines + ['}'])


def cell(root, i, value, style, x, y, w, h):
    c = ET.SubElement(root, 'mxCell', id=i, value=value, style=style, parent='1', vertex='1')
    ET.SubElement(c, 'mxGeometry', x=str(round(x, 2)), y=str(round(y, 2)), width=str(round(w, 2)), height=str(round(h, 2)), **{'as': 'geometry'})
    return c


def page(mxfile, model, protected, layout):
    suffix = 'protected' if protected else 'as-is'
    name = f"{model['slug'][:2]} — {'Меры' if protected else 'As-Is'}"
    diagram = ET.SubElement(mxfile, 'diagram', name=name, id=model['slug'] + '-' + suffix)
    xmin, ymin, xmax, ymax = map(float, layout['bb'].split(','))
    W, H = xmax - xmin + 40, ymax - ymin + 40
    graph = ET.SubElement(diagram, 'mxGraphModel', grid='1', gridSize='10', page='1', pageScale='1', pageWidth=str(round(W)), pageHeight=str(round(H)), math='0', shadow='0')
    root = ET.SubElement(graph, 'root')
    ET.SubElement(root, 'mxCell', id='0')
    ET.SubElement(root, 'mxCell', id='1', parent='0')
    def point(x, y):
        return x - xmin + 20, ymax - y + 20
    for obj in layout['objects']:
        if obj.get('name') == 'cluster_company':
            a, b, c, d = map(float, obj['bb'].split(','))
            x, y = point(a, d)
            cell(root, 'boundary', 'Управляемый контур компании (не отдельные серверы)', 'fillColor=none;strokeColor=#94a3b8;dashed=1;align=center;verticalAlign=top;fontSize=12;whiteSpace=wrap;', x, y, c-a, d-b)
    cell(root, 'heading', model['title'] + '\n' + ('Меры защиты — предложения' if protected else 'Текущее состояние — модель As-Is') + '\nОвал: операция · Прямоугольник: участник · Две линии: хранилище\n[Д] и пунктир: допущение · K1–K9: меры в data-protection.md', 'text;html=0;align=center;verticalAlign=middle;whiteSpace=wrap;fontSize=15;', 20, 20, W-40, 92)
    positions = {o['name']: o for o in layout['objects'] if 'pos' in o and 'width' in o}
    gids = {o['_gvid']: o['name'] for o in layout['objects'] if 'pos' in o}
    for n in model['nodes']:
        i, kind, title, extra = n
        obj = positions[i]
        x, y = map(float, obj['pos'].split(','))
        w, h = float(obj['width'])*72, float(obj['height'])*72
        x, y = point(x-w/2, y+h/2)
        styles = {
            'entity': 'shape=rectangle;fillColor=#f1f3f5;strokeColor=#333333;',
            'process': 'shape=ellipse;fillColor=' + ('#e8f5ee' if protected else '#e7f0fb') + ';strokeColor=#333333;',
            'store': 'shape=partialRectangle;top=1;bottom=1;left=0;right=0;fillColor=none;strokeColor=#333333;',
        }
        cell(root, i, node_label(n, protected), styles[kind]+'whiteSpace=wrap;html=0;fontFamily=DejaVu Sans;fontSize=13;align=center;verticalAlign=middle;', x, y, w, h)
    for idx, edge in enumerate(layout['edges']):
        f = next(f for f in model['flows'] if f[0] == edge['label'].split(':', 1)[0])
        i, a, b, label, status, detail, controls = f
        assert gids[edge['tail']] == a and gids[edge['head']] == b
        c = ET.SubElement(root, 'mxCell', id=i, value='', parent='1', edge='1', source=a, target=b,
                          style='endArrow=block;endFill=1;html=0;strokeWidth=1;rounded=0;' + ('dashed=1;' if status=='Д' else ''))
        geo = ET.SubElement(c, 'mxGeometry', relative='1', **{'as': 'geometry'})
        pts = []
        for draw in edge.get('_draw_', []):
            if draw['op'] == 'b':
                for p in draw['points']:
                    q = point(*p)
                    if not pts or q != pts[-1]:
                        pts.append(q)
        if len(pts)>2:
            arr = ET.SubElement(geo, 'Array', **{'as': 'points'})
            for x, y in pts[1:-1]:
                ET.SubElement(arr, 'mxPoint', x=str(round(x,2)), y=str(round(y,2)))
        lx, ly = point(*map(float, edge['lp'].split(',')))
        label = f'{i}: ' + '\n'.join(textwrap.wrap(label, width=29, break_long_words=False, break_on_hyphens=False)) + (' [Д]' if status == 'Д' else '')
        if protected:
            label += '\n' + controls
        draw_text = [d for d in edge.get('_ldraw_', []) if d['op']=='T']
        width = max([d.get('width',0) for d in draw_text] + [100]) + 8
        height = 15 * len(label.split('\n')) + 5
        cell(root, i+'-label', label, 'text;html=0;whiteSpace=wrap;align=center;verticalAlign=middle;fontFamily=DejaVu Sans;fontSize=11;fillColor=#ffffff;fontColor='+('#166534' if protected else '#333333')+';', lx-width/2, ly-height/2, width, height)


def register():
    parts = ['# Реестр потоков данных', '',
             'Коды соответствуют стрелкам в [draw.io](data-flows.drawio) и SVG. `П` — поток или связь прямо указаны в материалах, `Л` — логически восстановленная операция, `Д` — допущение для проверки. Статус связи не подтверждает точный состав полей: уточнения приведены в последнем столбце.', '',
             'Все коды K обозначают предлагаемые меры из [правил защиты](data-protection.md#меры-на-этапах-потока). Известная действующая мера — доменная аутентификация. Каждая версия «Меры» сохраняет коды и направления исходных потоков; подписи показывают ограничения на передачу и обработку.', '',
             'Хранилища D1, D2, D3, D5 и D6 — файлы общего диска; D4/D7 — файловые базы 1С на сервере; D8 — Exchange на том же физическом сервере. D9 — предполагаемая рабочая область аналитика. Отдельные изображения одного D-кода обозначают одно логическое хранилище, а не разные копии.', '']
    for m in MODELS:
        parts += [f"## {m['slug'][:2]}. {m['title']}", '', m['context'], '', m['boundary'], '',
                  f"[As-Is](diagrams/{m['slug']}-as-is.svg) · [Меры защиты](diagrams/{m['slug']}-protected.svg)", '',
                  '| Поток | Откуда → куда | Данные | Статус | Предлагаемые меры | Операция и ограничения |',
                  '| --- | --- | --- | --- | --- | --- |']
        names = {n[0]: n[2] for n in m['nodes']}
        for i, a, b, label, status, detail, controls in m['flows']:
            values = [i, names[a]+' → '+names[b], label, status, controls, detail]
            parts.append('| ' + ' | '.join(v.replace('\n', ' ').replace('|','\\|') for v in values) + ' |')
        parts.append('')
    return '\n'.join(parts)


def validate_models():
    used = set()
    for m in MODELS:
        nodes = {n[0]: n[1] for n in m['nodes']}
        ins, outs = set(), set()
        for i, a, b, label, status, detail, controls in m['flows']:
            assert i not in used and a in nodes and b in nodes
            used.add(i)
            assert 'process' in (nodes[a], nodes[b]), 'A flow must pass through a process'
            assert label and detail and status in ('П','Л','Д') and controls
            ins.add(b)
            outs.add(a)
        for i, kind in nodes.items():
            if kind == 'process':
                assert i in ins and i in outs, f'{i}: process needs input and output'
            assert i in ins or i in outs, f'{i}: disconnected node'
    return len(used)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview-dir', type=Path, help='Optional directory for PNG previews')
    args = parser.parse_args()
    count = validate_models()
    out = ROOT / 'diagrams'
    out.mkdir(exist_ok=True)
    if args.preview_dir:
        args.preview_dir.mkdir(parents=True, exist_ok=True)
    mxfile = ET.Element('mxfile', host='app.diagrams.net', version='24.7.17', type='device')
    with tempfile.TemporaryDirectory(prefix='medikamente-dfd-') as td:
        for model in MODELS:
            for protected in (False, True):
                name = model['slug'] + ('-protected' if protected else '-as-is')
                source = Path(td) / (name+'.dot')
                source.write_text(dot_source(model, protected), encoding='utf-8')
                subprocess.run(['dot','-Tsvg',str(source),'-o',str(out/(name+'.svg'))], check=True)
                layout = json.loads(subprocess.check_output(['dot','-Tjson',str(source)]))
                page(mxfile, model, protected, layout)
                if args.preview_dir:
                    subprocess.run(['dot','-Tpng',str(source),'-o',str(args.preview_dir/(name+'.png'))], check=True)
    ET.indent(mxfile, space='  ')
    ET.ElementTree(mxfile).write(ROOT/'data-flows.drawio', encoding='utf-8', xml_declaration=True)
    (ROOT/'data-flows.md').write_text(register()+'\n', encoding='utf-8')
    print(f'Generated {len(MODELS)*2} diagrams and {count} flow descriptions.')


if __name__ == '__main__':
    main()
