#!/usr/bin/env python3
"""DFD definitions and SVG export. Run with Python 3 and Graphviz (dot)."""

from pathlib import Path

from diagram_layout import render_svg

DIAGRAMS_DIR = Path(__file__).resolve().parent / "diagrams"

p1_as_is = {'title': 'DFD Процесс 1 (As-Is): Первичная регистрация пациента и оформление документов',
 'subtitle': 'Текущее состояние: ручной сбор избыточных ПДн, хранение сканов на общем сетевом диске без '
             'шифрования и разграничения прав',
 'elements': [{'type': 'entity',
               'id': 'E1',
               'title': 'Пациент (Patient)',
               'subtitle': 'Субъект ПДн\nОчное обращение'},
              {'type': 'entity',
               'id': 'E2',
               'title': 'Ресепшен (Receptionist)',
               'subtitle': 'Сотрудник клиники\n3 человека'},
              {'type': 'process',
               'id': '1.1',
               'title': 'Сбор ПДн и анкеты',
               'subtitle': 'Ручное заполнение бланка:\n'
                           'паспорт, контакты, работа,\n'
                           'хронические заболевания',
               'status': 'vulnerable',
               'badge': 'Избыточный сбор'},
              {'type': 'process',
               'id': '1.2',
               'title': 'Ведение Excel-реестра',
               'subtitle': 'Внесение данных пациента\nв единый неструктурированный\nфайл Patients.xlsx',
               'status': 'vulnerable',
               'badge': 'Нет контроля прав'},
              {'type': 'process',
               'id': '1.3',
               'title': 'Сканирование документов',
               'subtitle': 'МФУ -> скан паспорта,\nдоговора и согласия\nв JPG / PDF без учета',
               'status': 'vulnerable',
               'badge': 'Теневые сканы'},
              {'type': 'store',
               'id': 'D1',
               'title': 'Файловый диск: Patients.xlsx',
               'subtitle': 'Общий каталог SMB/CIFS\n'
                           'Доступен всем доменным пользователям\n'
                           'Отсутствует шифрование и аудит',
               'status': 'vulnerable',
               'badge': 'Риск УЗ-1'},
              {'type': 'store',
               'id': 'D2',
               'title': 'Файловый диск: \\\\Pacients\\*',
               'subtitle': 'Папки: Pacient1-FIO-BD\n'
                           'Сканы паспортов, согласий, анкет\n'
                           'Нет версионирования и удаления',
               'status': 'vulnerable',
               'badge': 'Нарушение 152-ФЗ'}],
 'flows': [{'label': 'Бумажная анкета:\nФИО, паспорт, телефон,\nместо работы/учебы, анамнез',
            'style': 'vulnerable',
            'source': 'E1',
            'target': '1.1'},
           {'label': 'Выдача бланков\nи договоров', 'style': 'normal', 'source': 'E2', 'target': 'E1'},
           {'label': 'Ручной ввод\nФИО и контактов', 'style': 'normal', 'source': 'E2', 'target': '1.2'},
           {'label': 'Сканирование\nдокументов на МФУ',
            'style': 'normal',
            'source': 'E2',
            'target': '1.3'},
           {'label': 'Запись строки\nв открытый Excel',
            'style': 'vulnerable',
            'source': '1.2',
            'target': 'D1'},
           {'label': 'Сохранение JPG/PDF\nпо SMB без шифрования',
            'style': 'vulnerable',
            'source': '1.3',
            'target': 'D2'}]}

p1_to_be = {'title': 'DFD Процесс 1 (To-Be): Защищенная регистрация и онбординг пациента',
 'subtitle': 'Целевое состояние: Data Minimization, TLS 1.3, Keycloak RBAC/ABAC, PostgreSQL TDE, MinIO '
             'S3 SSE-KMS, тегирование PII',
 'elements': [{'type': 'entity',
               'id': 'E1',
               'title': 'Пациент (Client)',
               'subtitle': 'Web-портал / App / Планшет\nСамостоятельный ввод'},
              {'type': 'entity',
               'id': 'E2',
               'title': 'Ресепшен (Staff)',
               'subtitle': 'АРМ сотрудника ресепшена\nРоль: Receptionist (RBAC)'},
              {'type': 'process',
               'id': '1.1',
               'title': 'Минимизированный сбор ПДн',
               'subtitle': 'Исключены место работы/учебы\n'
                           'Только необходимые ФИО, телефон,\n'
                           'паспорт и электронное ИДС',
               'status': 'secure',
               'badge': 'Data Minimization'},
              {'type': 'process',
               'id': '1.2',
               'title': 'Аутентификация и валидация',
               'subtitle': 'Kong API Gateway + WAF\n'
                           'Keycloak IdP (JWT Bearer)\n'
                           'Проверка согласия на обработку',
               'status': 'secure',
               'badge': 'OAuth2 / mTLS'},
              {'type': 'process',
               'id': '1.3',
               'title': 'Псевдонимизация и тегирование',
               'subtitle': 'Генерация patient_uuid\n'
                           'Маркировка: PII_CONFIDENTIAL\n'
                           'Политики OPA + OpenMetadata',
               'status': 'secure',
               'badge': 'Data Tagging Engine'},
              {'type': 'store',
               'id': 'D1',
               'title': 'Patient DB (PostgreSQL)',
               'subtitle': 'Шифрование TDE / pgcrypto\n'
                           'Row-Level Security (RLS)\n'
                           'UUID связка, аудит чтения',
               'status': 'secure',
               'badge': 'AES-256 / УЗ-1'},
              {'type': 'store',
               'id': 'D2',
               'title': 'Doc Storage (MinIO S3)',
               'subtitle': 'Электронные согласия и сканы\n'
                           'Server-Side Encryption (SSE-KMS)\n'
                           'Object Versioning & Retention',
               'status': 'secure',
               'badge': 'Vault KMS'},
              {'type': 'store',
               'id': 'D3',
               'title': 'Audit & Event Store (Kafka)',
               'subtitle': 'Централизованный Audit Log\n'
                           'Шина сообщений Kafka mTLS\n'
                           'Data Lineage фиксация',
               'status': 'secure',
               'badge': 'Vector / OpenSearch'},
              {'type': 'security_badge',
               'id': 'SEC1',
               'title': 'Меры безопасности To-Be',
               'subtitle': '• TLS 1.3 шифрование\n'
                           '• RBAC/ABAC доступ\n'
                           '• Токенизация patient_id\n'
                           '• Тегирование PII\n'
                           '• Автоматический аудит\n'
                           '• Поддержка ст. 21 152-ФЗ\n'
                           '  (удаление по запросу)'}],
 'flows': [{'label': 'HTTPS TLS 1.3:\nФИО, контакты, паспорт, ИДС',
            'style': 'secure',
            'source': 'E1',
            'target': '1.1'},
           {'label': 'Авторизованный доступ\nк АРМ (Keycloak 2FA)',
            'style': 'secure',
            'source': 'E2',
            'target': '1.2'},
           {'label': 'Передача профиля\nчерез API Gateway',
            'style': 'secure',
            'source': '1.1',
            'target': '1.2'},
           {'label': 'Обогащение тегами\nи генерация UUID',
            'style': 'secure',
            'source': '1.2',
            'target': '1.3'},
           {'label': 'Запись карточки\nпациента (TDE)',
            'style': 'secure',
            'source': '1.1',
            'target': 'D1'},
           {'label': 'Загрузка сканов\nс тегом PII_FILE',
            'style': 'secure',
            'source': '1.2',
            'target': 'D2'},
           {'label': 'Событие: PatientCreated\n(Audit Lineage)',
            'style': 'secure',
            'source': '1.3',
            'target': 'D3'}]}

p2_as_is = {'title': 'DFD Процесс 2 (As-Is): Запись пациента на приём к специалисту',
 'subtitle': 'Текущее состояние: открытые Excel-файлы расписаний по докторам, раскрытие врачебной '
             'тайны, коллизии блокировок',
 'elements': [{'type': 'entity',
               'id': 'E1',
               'title': 'Пациент (Patient)',
               'subtitle': 'Обращение по телефону\nили лично на стойку'},
              {'type': 'entity',
               'id': 'E2',
               'title': 'Ресепшен (Receptionist)',
               'subtitle': 'Администратор ведет запись\nв файлы расписаний'},
              {'type': 'entity',
               'id': 'E3',
               'title': 'Врач (Doctor)',
               'subtitle': 'Медицинский специалист\n15 сотрудников'},
              {'type': 'process',
               'id': '2.1',
               'title': 'Проверка расписания',
               'subtitle': 'Поиск свободного слота\nв открытом файле Excel\nJournal-Doctor-FIO.xlsx',
               'status': 'vulnerable',
               'badge': 'Коллизии файлов'},
              {'type': 'process',
               'id': '2.2',
               'title': 'Внесение записи на прием',
               'subtitle': 'Ручной ввод ФИО, телефона,\n'
                           'специальности и причины\n'
                           'визита в ячейку таблицы',
               'status': 'vulnerable',
               'badge': 'Утечка врачебной тайны'},
              {'type': 'store',
               'id': 'D1',
               'title': 'Файловый диск: \\\\Journals\\*',
               'subtitle': 'Таблицы: Journal-Doctor-FIO.xlsx\n'
                           'Каждый врач и администратор имеет\n'
                           'доступ к расписанию ВСЕХ врачей клиники!\n'
                           'Нарушение ст. 13 323-ФЗ (врачебная тайна)',
               'status': 'vulnerable',
               'badge': 'Критический риск'}],
 'flows': [{'label': 'Запрос записи: специальность,\nФИО, телефон, симптомы',
            'style': 'vulnerable',
            'source': 'E1',
            'target': '2.1'},
           {'label': 'Открытие файла Excel\nдоктора через SMB',
            'style': 'normal',
            'source': 'E2',
            'target': '2.1'},
           {'label': 'Выбор свободного\nслота времени',
            'style': 'normal',
            'source': '2.1',
            'target': '2.2'},
           {'label': 'Сохранение файла\nJournal-Doctor-FIO.xlsx',
            'style': 'vulnerable',
            'source': '2.2',
            'target': 'D1'},
           {'label': 'Врач открывает расписание\n(и может открыть чужие файлы!)',
            'style': 'vulnerable',
            'source': 'E3',
            'target': 'D1'}]}

p2_to_be = {'title': 'DFD Процесс 2 (To-Be): Автоматизированная запись на прием с RBAC/ABAC',
 'subtitle': 'Целевое состояние: ЛК пациента, RBAC изоляция журналов врачей, Kafka нотификации, '
             'токенизация appointments',
 'elements': [{'type': 'entity',
               'id': 'E1',
               'title': 'Пациент (Client)',
               'subtitle': 'Web-портал / Мобильное App\nАвтономная запись 24/7'},
              {'type': 'entity',
               'id': 'E2',
               'title': 'Ресепшен (Staff)',
               'subtitle': 'АРМ ресепшена\nТолько общие слоты'},
              {'type': 'entity',
               'id': 'E3',
               'title': 'Врач (Doctor)',
               'subtitle': 'АРМ врача (RBAC/ABAC)\nВидит ТОЛЬКО своих пациентов'},
              {'type': 'process',
               'id': '2.1',
               'title': 'Запрос расписания (API)',
               'subtitle': 'Фильтрация доступных слотов\n'
                           'Без раскрытия чужих данных\n'
                           'Rate limiting + WAF',
               'status': 'secure',
               'badge': 'Data Minimization'},
              {'type': 'process',
               'id': '2.2',
               'title': 'Бронирование визита',
               'subtitle': 'Appointment Service (OLTP)\n'
                           'Атомарная транзакция в PostgreSQL\n'
                           'Тег: PHI_APPOINTMENT',
               'status': 'secure',
               'badge': 'Zero Collisions'},
              {'type': 'process',
               'id': '2.3',
               'title': 'Оповещения и напоминания',
               'subtitle': 'Notification Service (Kafka)\n'
                           'SMS/Push за 24ч до приема\n'
                           'Без раскрытия диагноза',
               'status': 'secure',
               'badge': 'Privacy-preserving'},
              {'type': 'store',
               'id': 'D1',
               'title': 'Appointment DB (PostgreSQL)',
               'subtitle': 'Слоты, patient_uuid, doctor_id\n'
                           'ABAC правила доступа (OPA)\n'
                           'Исключены коллизии блокировок',
               'status': 'secure',
               'badge': 'TDE / RLS'},
              {'type': 'store',
               'id': 'D2',
               'title': 'Message Broker (Kafka mTLS)',
               'subtitle': 'Топик appointments.events\n'
                           'События: Created, Confirmed, Cancelled\n'
                           'Шифрование payload + audit',
               'status': 'secure',
               'badge': 'Audit & Events'},
              {'type': 'security_badge',
               'id': 'SEC1',
               'title': 'Защитные механизмы',
               'subtitle': '• Врач видит ТОЛЬКО\n'
                           '  свое расписание (ABAC)\n'
                           '• Пациент видит только\n'
                           '  свободные временные окна\n'
                           '• Нет утечки диагнозов\n'
                           '• Логирование в SIEM\n'
                           '• Высокая доступность'}],
 'flows': [{'label': 'HTTPS TLS 1.3: Поиск врача/слота',
            'style': 'secure',
            'source': 'E1',
            'target': '2.1'},
           {'label': 'Создание записи с ресепшена', 'style': 'secure', 'source': 'E2', 'target': '2.2'},
           {'label': 'Запрос журнала (только свой doctor_id)',
            'style': 'secure',
            'source': 'E3',
            'target': '2.3'},
           {'label': 'Выбор интервала', 'style': 'secure', 'source': '2.1', 'target': '2.2'},
           {'label': 'Фиксация брони в БД', 'style': 'secure', 'source': '2.2', 'target': 'D1'},
           {'label': 'Инициация события', 'style': 'secure', 'source': '2.2', 'target': '2.3'},
           {'label': 'Публикация брони в Kafka', 'style': 'secure', 'source': '2.3', 'target': 'D2'}]}

p3_as_is = {'title': 'DFD Процесс 3 (As-Is): Проведение медицинского приёма и ведение медкарты',
 'subtitle': 'Текущее состояние: файлы Word/Excel на файловом сервере, нет ЭЦП, нет версионирования, '
             'доступ открыт всей сети',
 'elements': [{'type': 'entity',
               'id': 'E1',
               'title': 'Пациент (Patient)',
               'subtitle': 'Очный прием в кабинете\nОпрос, осмотр'},
              {'type': 'entity',
               'id': 'E2',
               'title': 'Врач (Doctor)',
               'subtitle': 'Медицинский специалист\nПК в локальной сети'},
              {'type': 'process',
               'id': '3.1',
               'title': 'Поиск медкарты в проводнике',
               'subtitle': 'Открытие сетевой папки\n'
                           '\\\\Pacients\\Pacient1-FIO-BD\n'
                           'Чтение Word/PDF файлов',
               'status': 'vulnerable',
               'badge': 'Нет аудита чтения'},
              {'type': 'process',
               'id': '3.2',
               'title': 'Осмотр и оформление карты',
               'subtitle': 'Внесение жалоб, диагноза (МКБ),\n'
                           'назначений в локальный файл Word\n'
                           'БЕЗ цифровой подписи (ЭЦП)',
               'status': 'vulnerable',
               'badge': 'Нет юр. значимости'},
              {'type': 'process',
               'id': '3.3',
               'title': 'Печать заключений',
               'subtitle': 'Вывод на локальный принтер\n'
                           'бумажного листа с диагнозом\n'
                           'и назначением лечения',
               'status': 'normal',
               'badge': 'Бумажный след'},
              {'type': 'store',
               'id': 'D1',
               'title': 'Файловый диск: Медкарты пациентов',
               'subtitle': 'Каталоги \\\\Pacients\\Pacient-FIO-BD\\\n'
                           'Файлы DOCX, PDF, XLSX, JPG\n'
                           '• Доступен любому ПК в офисе\n'
                           '• Нет неизменяемости (WORM)\n'
                           '• Нет журналирования (кто читал?)\n'
                           '• Нарушение 323-ФЗ и УЗ-1 (ФСТЭК № 21)',
               'status': 'vulnerable',
               'badge': 'Критическая уязвимость'}],
 'flows': [{'label': 'Озвучивание жалоб,\nанамнез, симптомы',
            'style': 'vulnerable',
            'source': 'E1',
            'target': '3.1'},
           {'label': 'Поиск папки пациента\nв проводнике Windows',
            'style': 'normal',
            'source': 'E2',
            'target': '3.1'},
           {'label': 'Загрузка старых записей\nв Word без аудита',
            'style': 'vulnerable',
            'source': '3.1',
            'target': '3.2'},
           {'label': 'Перезапись файла DOCX\nпо открытому SMB',
            'style': 'vulnerable',
            'source': '3.2',
            'target': 'D1'},
           {'label': 'Отправка на печать', 'style': 'normal', 'source': '3.2', 'target': '3.3'},
           {'label': 'Бумажное заключение пациенту',
            'style': 'normal',
            'source': '3.3',
            'target': 'E1'}]}

p3_to_be = {'title': 'DFD Процесс 3 (To-Be): Защищенная электронная медицинская карта (ЭМК / EHR)',
 'subtitle': 'Целевое состояние: ABAC (доступ только на время визита), УКЭП врача, стандарты FHIR, S3 '
             'WORM, SIEM-аудит',
 'elements': [{'type': 'entity',
               'id': 'E1',
               'title': 'Пациент (Patient)',
               'subtitle': 'Субъект ПДн\nЛичный кабинет (ЛК)'},
              {'type': 'entity',
               'id': 'E2',
               'title': 'Врач (Doctor)',
               'subtitle': 'АРМ врача\nАппаратный токен УКЭП'},
              {'type': 'process',
               'id': '3.1',
               'title': 'ABAC авторизация доступа',
               'subtitle': 'OPA Policy Engine:\n'
                           'доступ к медкарте ТОЛЬКО при\n'
                           'наличии активной записи на прием',
               'status': 'secure',
               'badge': 'Strict ABAC'},
              {'type': 'process',
               'id': '3.2',
               'title': 'Ведение протокола (EHR)',
               'subtitle': 'Структурированный формат FHIR\n'
                           'Тег: PHI_SPECIAL_RESTRICTED\n'
                           'Подписание УКЭП врача (947н)',
               'status': 'secure',
               'badge': 'УКЭП / Минздрав 947н'},
              {'type': 'process',
               'id': '3.3',
               'title': 'Иммутабельное архивирование',
               'subtitle': 'Шифрование AES-256 (TDE)\n'
                           'Политика неизменяемости (WORM)\n'
                           'Запрет скрытого редактирования',
               'status': 'secure',
               'badge': 'WORM / Immutability'},
              {'type': 'store',
               'id': 'D1',
               'title': 'EHR Clinical DB (PostgreSQL)',
               'subtitle': 'Медицинские записи, диагнозы МКБ\n'
                           'Шифрование pgcrypto/TDE\n'
                           'Маскирование для не-врачей',
               'status': 'secure',
               'badge': 'PostgreSQL TDE'},
              {'type': 'store',
               'id': 'D2',
               'title': 'Medical Docs (MinIO S3 SSE)',
               'subtitle': 'Подписанные PDF/A, снимки, ЭКГ\n'
                           'KMS Envelope Encryption\n'
                           'Object Lock (Immutability)',
               'status': 'secure',
               'badge': 'SSE-KMS / WORM'},
              {'type': 'store',
               'id': 'D3',
               'title': 'SIEM & Audit Vault',
               'subtitle': 'Полная фиксация каждого чтения!\n'
                           'Vector -> OpenSearch -> Wazuh\n'
                           'Срок хранения логов 5 лет',
               'status': 'secure',
               'badge': 'Неотслеживаемость исключена'},
              {'type': 'security_badge',
               'id': 'SEC1',
               'title': 'Гарантии безопасности',
               'subtitle': '• Врач другой специальности\n'
                           '  НЕ МОЖЕТ открыть карту\n'
                           '• Каждая запись подписана\n'
                           '  личной УКЭП врача\n'
                           '• Невозможно подделать\n'
                           '  или удалить историю болезни\n'
                           '• 100% аудит просмотров\n'
                           '• Полное соответствие 323-ФЗ'}],
 'flows': [{'label': 'Запрос ЭМК пациента (mTLS)', 'style': 'secure', 'source': 'E2', 'target': '3.1'},
           {'label': 'Разрешение OPA (ABAC OK)', 'style': 'secure', 'source': '3.1', 'target': '3.2'},
           {'label': 'Чтение медкарты (Audit Logged)',
            'style': 'secure',
            'source': '3.1',
            'target': 'D1'},
           {'label': 'Сохранение протокола + УКЭП', 'style': 'secure', 'source': '3.2', 'target': 'D2'},
           {'label': 'Блокировка изменений', 'style': 'secure', 'source': '3.2', 'target': '3.3'},
           {'label': 'Отправка лога в SIEM', 'style': 'secure', 'source': '3.3', 'target': 'D3'},
           {'label': 'Доступ к своей карте в ЛК', 'style': 'secure', 'source': '3.1', 'target': 'E1'}]}

p4_as_is = {'title': 'DFD Процесс 4 (As-Is): Направление и получение анализов из лаборатории',
 'subtitle': 'Текущее состояние: открытый Exchange e-mail, незащищенные реестры анализов, отсутствие '
             'деперсонализации биоматериала',
 'elements': [{'type': 'entity',
               'id': 'E1',
               'title': 'Пациент (Patient)',
               'subtitle': 'Сдает биоматериал\nв процедурном кабинете'},
              {'type': 'entity',
               'id': 'E2',
               'title': 'Медсестра / Ресепшен',
               'subtitle': 'Оформляет суточный реестр\nи отправляет пробирки'},
              {'type': 'entity',
               'id': 'E3',
               'title': 'Внешняя лаборатория',
               'subtitle': 'Партнерская лаборатория\nОбмен через Exchange / файлы'},
              {'type': 'process',
               'id': '4.1',
               'title': 'Ведение реестра анализов',
               'subtitle': 'Внесение ФИО, даты, видов\nисследований в Excel\nRegistryByDate.xlsx',
               'status': 'vulnerable',
               'badge': 'Нет шифрования'},
              {'type': 'process',
               'id': '4.2',
               'title': 'Передача реестра партнеру',
               'subtitle': 'Отправка списка пациентов\nи забор пробирок курьером\nбез деперсонализации',
               'status': 'vulnerable',
               'badge': 'Нарушение тайны'},
              {'type': 'process',
               'id': '4.3',
               'title': 'Прием результатов (e-mail)',
               'subtitle': 'Получение PDF/XLS по Exchange,\n'
                           'ручное копирование в папки\n'
                           'пациентов на файловом диске',
               'status': 'vulnerable',
               'badge': 'Открытый e-mail'},
              {'type': 'store',
               'id': 'D1',
               'title': 'Файловый диск: Laboratory Registry',
               'subtitle': 'Каталоги \\\\Laboratory Registry\\RegistryByDate.xlsx\n'
                           '• Доступен всем сотрудникам\n'
                           '• Содержит ФИО + ВИЧ, гепатиты, онкомаркеры!\n'
                           '• Нарушение ст. 10 152-ФЗ и ст. 13 323-ФЗ',
               'status': 'vulnerable',
               'badge': 'Утечка спецкатегорий'}],
 'flows': [{'label': 'Забор биоматериала (ФИО на пробирке)',
            'style': 'vulnerable',
            'source': 'E1',
            'target': '4.1'},
           {'label': 'Ручной ввод в RegistryByDate.xlsx',
            'style': 'normal',
            'source': 'E2',
            'target': '4.1'},
           {'label': 'Запись строки в Excel', 'style': 'vulnerable', 'source': '4.1', 'target': 'D1'},
           {'label': 'Формирование списка отправки',
            'style': 'normal',
            'source': '4.1',
            'target': '4.2'},
           {'label': 'Отправка реестра с ФИО курьеру',
            'style': 'vulnerable',
            'source': '4.2',
            'target': 'E3'},
           {'label': 'Результаты анализов по незашифрованному Exchange',
            'style': 'vulnerable',
            'source': 'E3',
            'target': '4.3'},
           {'label': 'Раскладывание PDF по папкам \\\\Pacients\\',
            'style': 'vulnerable',
            'source': '4.3',
            'target': 'D1'}]}

p4_to_be = {'title': 'DFD Процесс 4 (To-Be): Защищенная интеграция с лабораторией (Lab API / mTLS)',
 'subtitle': 'Целевое состояние: деперсонализация биоматериала (barcode token), mTLS API контракты, '
             'Webhook, исключение утечек',
 'elements': [{'type': 'entity',
               'id': 'E1',
               'title': 'Пациент (Patient)',
               'subtitle': 'Сдает биоматериал\nРезультаты в ЛК'},
              {'type': 'entity',
               'id': 'E2',
               'title': 'Процедурный кабинет',
               'subtitle': 'Медсестра (АРМ)\nМаркировка пробирок'},
              {'type': 'entity',
               'id': 'E3',
               'title': 'Внешняя лаборатория',
               'subtitle': 'Lab API Partner\nИнтеграция по стандарту'},
              {'type': 'process',
               'id': '4.1',
               'title': 'Деперсонализация заказа',
               'subtitle': 'Генерация sample_uuid и barcode.\n'
                           'Лаборатории передается ТОЛЬКО код,\n'
                           'пол, возраст (без ФИО и паспорта)',
               'status': 'secure',
               'badge': 'Pseudonymization'},
              {'type': 'process',
               'id': '4.2',
               'title': 'Защищенный API Gateway',
               'subtitle': 'Взаимная аутентификация mTLS\n'
                           'Строгий OpenAPI контракт\n'
                           'Валидация входящей схемы',
               'status': 'secure',
               'badge': 'mTLS / Zero Trust'},
              {'type': 'process',
               'id': '4.3',
               'title': 'Реидентификация и доставка',
               'subtitle': 'Сопоставление sample_uuid -> patient_uuid\n'
                           'в закрытом изолированном Vault.\n'
                           'Тег: PHI_LAB_RESULT',
               'status': 'secure',
               'badge': 'Tokenization Vault'},
              {'type': 'store',
               'id': 'D1',
               'title': 'Token Vault (HashiCorp)',
               'subtitle': 'Таблица связки: barcode <-> patient_uuid\n'
                           'Доступна ТОЛЬКО Lab Service\n'
                           'Изолирована от внешнего контура',
               'status': 'secure',
               'badge': 'Isolated Vault'},
              {'type': 'store',
               'id': 'D2',
               'title': 'Lab Orders DB (PostgreSQL)',
               'subtitle': 'Статусы заказов, даты готовности\nШифрование TDE\nБез персональных данных',
               'status': 'secure',
               'badge': 'Anonymized Orders'},
              {'type': 'store',
               'id': 'D3',
               'title': 'Results Storage (MinIO S3)',
               'subtitle': 'Зашифрованные PDF бланки\n'
                           'SSE-KMS шифрование\n'
                           'Доступ пациенту только к своим!',
               'status': 'secure',
               'badge': 'SSE-KMS / RLS'},
              {'type': 'security_badge',
               'id': 'SEC1',
               'title': 'Принципы защиты',
               'subtitle': '• Партнер НЕ ЗНАЕТ ФИО\n'
                           '  пациента (только barcode)\n'
                           '• Никаких Excel реестров\n'
                           '• Никаких пересылок по mail\n'
                           '• Двусторонний mTLS\n'
                           '• Исключен просмотр чужих\n'
                           '  анализов другими клиентами'}],
 'flows': [{'label': 'Создание заказа на исследование',
            'style': 'secure',
            'source': 'E2',
            'target': '4.1'},
           {'label': 'Сохранение токена barcode', 'style': 'secure', 'source': '4.1', 'target': 'D1'},
           {'label': 'Передача деперсонализированного заказа',
            'style': 'secure',
            'source': '4.1',
            'target': '4.2'},
           {'label': 'mTLS API: отправка barcode + анализ',
            'style': 'secure',
            'source': '4.2',
            'target': 'E3'},
           {'label': 'mTLS Webhook: результат с barcode',
            'style': 'secure',
            'source': 'E3',
            'target': '4.3'},
           {'label': 'Валидация подписи лаборатории',
            'style': 'secure',
            'source': '4.2',
            'target': '4.3'},
           {'label': 'Сохранение PDF в MinIO S3', 'style': 'secure', 'source': '4.3', 'target': 'D3'},
           {'label': 'Push-уведомление в ЛК пациента',
            'style': 'secure',
            'source': '4.1',
            'target': 'E1'}]}

p5_as_is = {'title': 'DFD Процесс 5 (As-Is): Оплата медицинских услуг и фискализация',
 'subtitle': 'Текущее состояние: двойной учет (Excel + 1С), незащищенный протокол ККМ, файловая БД '
             '«1С:Бухгалтерия»',
 'elements': [{'type': 'entity',
               'id': 'E1',
               'title': 'Пациент (Patient)',
               'subtitle': 'Оплата на кассе\nналичные / карта'},
              {'type': 'entity',
               'id': 'E2',
               'title': 'Кассир (Cashier)',
               'subtitle': '3 сотрудника кассы\nДвойной учет'},
              {'type': 'entity',
               'id': 'E3',
               'title': 'ККМ (Кассовый аппарат)',
               'subtitle': 'Контрольно-кассовая машина\nСвязь по TCP/IP OLE'},
              {'type': 'process',
               'id': '5.1',
               'title': 'Прием платежа на кассе',
               'subtitle': 'Расчет стоимости услуг,\n'
                           'прием средств, ввод в локальный\n'
                           'файл Excel кассира',
               'status': 'vulnerable',
               'badge': 'Двойной учет'},
              {'type': 'process',
               'id': '5.2',
               'title': 'Пробитие чека через ККМ',
               'subtitle': 'Передача команды в ККМ по TCP/IP\n'
                           'через устаревшую OLE-компоненту\n'
                           'без шифрования трафика',
               'status': 'vulnerable',
               'badge': 'Незащищенный TCP/IP'},
              {'type': 'process',
               'id': '5.3',
               'title': 'Проводка в «1С:Бухгалтерия»',
               'subtitle': 'Ручное создание документа оплаты\n'
                           'в файловой базе 1С по сети SMB\n'
                           '(риск порчи базы при сбое сети)',
               'status': 'vulnerable',
               'badge': 'Файловый режим 1С'},
              {'type': 'store',
               'id': 'D1',
               'title': 'Локальный Excel кассира',
               'subtitle': 'Файлы учета платежей на ПК кассиров\n'
                           'Не централизованы, нет контроля доступа,\n'
                           'рассинхронизация с бухгалтерией',
               'status': 'vulnerable',
               'badge': 'Shadow Data'},
              {'type': 'store',
               'id': 'D2',
               'title': '1С:Бухгалтерия (файловая БД)',
               'subtitle': 'Сетевой путь: \\\\Server\\1C_Buh\\\n'
                           '• Блокировки таблиц\n'
                           '• Нет шифрования сетевого трафика\n'
                           '• Риск повреждения при скачке питания',
               'status': 'vulnerable',
               'badge': 'Риск потери данных'}],
 'flows': [{'label': 'Передача наличных / карты', 'style': 'normal', 'source': 'E1', 'target': '5.1'},
           {'label': 'Ввод суммы и ФИО в Excel', 'style': 'normal', 'source': 'E2', 'target': '5.1'},
           {'label': 'Сохранение кассового Excel',
            'style': 'vulnerable',
            'source': '5.1',
            'target': 'D1'},
           {'label': 'Команда на фискализацию', 'style': 'normal', 'source': '5.1', 'target': '5.2'},
           {'label': 'TCP/IP OLE (открытый трафик)',
            'style': 'vulnerable',
            'source': '5.2',
            'target': 'E3'},
           {'label': 'Выдача бумажного чека пациенту',
            'style': 'normal',
            'source': 'E3',
            'target': 'E1'},
           {'label': 'Синхронизация с 1С', 'style': 'normal', 'source': '5.2', 'target': '5.3'},
           {'label': 'Запись в файловую БД 1С по SMB',
            'style': 'vulnerable',
            'source': '5.3',
            'target': 'D2'}]}

p5_to_be = {'title': 'DFD Процесс 5 (To-Be): Защищенный платежный шлюз и фискализация (PCI DSS / 54-ФЗ)',
 'subtitle': 'Целевое состояние: Payment Gateway, СБП/Эквайринг (без хранения карт), ОФД, 1С '
             'клиент-сервер по API/Kafka',
 'elements': [{'type': 'entity',
               'id': 'E1',
               'title': 'Пациент (Client)',
               'subtitle': 'Оплата в App / ЛК / СБП\nили терминал на кассе'},
              {'type': 'entity',
               'id': 'E2',
               'title': 'Кассир / Ресепшен',
               'subtitle': 'АРМ кассира (RBAC)\nФормирование счетов'},
              {'type': 'entity',
               'id': 'E3',
               'title': 'Банк-эквайер / ОФД',
               'subtitle': 'Внешний шлюз эквайринга\nОператор фискальных данных'},
              {'type': 'process',
               'id': '5.1',
               'title': 'Billing & Invoicing Service',
               'subtitle': 'Формирование инвойса по заказу.\n'
                           'Связка order_uuid + сумма.\n'
                           'Маскирование мед. диагнозов',
               'status': 'secure',
               'badge': 'Data Minimization'},
              {'type': 'process',
               'id': '5.2',
               'title': 'Payment Gateway (PCI DSS)',
               'subtitle': 'Токенизация карт в банке.\n'
                           'Клиника НЕ хранит данные карт!\n'
                           'TLS 1.3 + криптоподпись webhook',
               'status': 'secure',
               'badge': 'PCI DSS Level 1'},
              {'type': 'process',
               'id': '5.3',
               'title': 'Fiscal & 1C Sync Service',
               'subtitle': 'Автоматическая фискализация (54-ФЗ),\n'
                           'электронный чек по SMS/email,\n'
                           'событие в Kafka для клиент-серверной 1С',
               'status': 'secure',
               'badge': '54-ФЗ / Kafka'},
              {'type': 'store',
               'id': 'D1',
               'title': 'Billing DB (PostgreSQL)',
               'subtitle': 'Счета, транзакции, фискальные теги\n'
                           'Шифрование TDE\n'
                           'Тег: FINANCIAL_CONFIDENTIAL',
               'status': 'secure',
               'badge': 'TDE / RLS'},
              {'type': 'store',
               'id': 'D2',
               'title': 'Audit & Kafka Pipeline',
               'subtitle': 'Топик billing.payments.completed\n'
                           'Асинхронная доставка в бухгалтерию\n'
                           'Идемпотентность транзакций',
               'status': 'secure',
               'badge': 'mTLS Kafka'},
              {'type': 'store',
               'id': 'D3',
               'title': '1С (Клиент-Сервер)',
               'subtitle': 'PostgreSQL база данных 1С\n'
                           'Интеграция по REST API/Kafka\n'
                           'Исключены файловые блокировки',
               'status': 'secure',
               'badge': 'Enterprise 1C'},
              {'type': 'security_badge',
               'id': 'SEC1',
               'title': 'Принципы защиты',
               'subtitle': '• Данные карт НЕ попадают\n'
                           '  на сервер клиники (СБП)\n'
                           '• Бухгалтерия видит только код\n'
                           '  услуги (без диагнозов!)\n'
                           '• Исключен теневой Excel\n'
                           '• Электронный чек в ОФД\n'
                           '• Клиент-серверная 1С'}],
 'flows': [{'label': 'Оплата: СБП / Карта / ЛК (TLS 1.3)',
            'style': 'secure',
            'source': 'E1',
            'target': '5.1'},
           {'label': 'Формирование счета на кассе', 'style': 'secure', 'source': 'E2', 'target': '5.1'},
           {'label': 'Передача платежного токена', 'style': 'secure', 'source': '5.1', 'target': '5.2'},
           {'label': 'Проведение платежа в банке', 'style': 'secure', 'source': '5.2', 'target': 'E3'},
           {'label': 'Webhook от банка + ОФД чек', 'style': 'secure', 'source': 'E3', 'target': '5.3'},
           {'label': 'Запись чека в Billing DB', 'style': 'secure', 'source': '5.1', 'target': 'D1'},
           {'label': 'Фискализация и нотификация', 'style': 'secure', 'source': '5.2', 'target': '5.3'},
           {'label': 'Событие PaymentSuccess в Kafka',
            'style': 'secure',
            'source': '5.3',
            'target': 'D2'},
           {'label': 'Синхронизация с 1С', 'style': 'secure', 'source': 'D2', 'target': 'D3'}]}

p6_as_is = {'title': 'DFD Процесс 6 (As-Is): Сбор аналитики, управленческая отчетность и бизнес-анализ',
 'subtitle': 'Текущее состояние: прямой сбор неанонимизированных Excel файлов на ноутбук аналитика '
             'через SMB, Jupyter Notebook',
 'elements': [{'type': 'entity',
               'id': 'E1',
               'title': 'Бизнес-аналитик (BA)',
               'subtitle': 'Сотрудник IT-отдела\nРабочий ноутбук'},
              {'type': 'entity',
               'id': 'E2',
               'title': 'Руководство клиники',
               'subtitle': 'Генеральный директор,\nГлавный врач'},
              {'type': 'process',
               'id': '6.1',
               'title': 'Прямое копирование файлов',
               'subtitle': 'Копирование Excel баз пациентов,\n'
                           'журналов и реестров анализов\n'
                           'по SMB на личный ноутбук',
               'status': 'vulnerable',
               'badge': 'Shadow Analytics'},
              {'type': 'process',
               'id': '6.2',
               'title': 'Расчеты в Jupyter Notebook',
               'subtitle': 'Запуск локальных Python скриптов\n'
                           'обработки сырых данных (ФИО, суммы,\n'
                           'диагнозы) БЕЗ обезличивания',
               'status': 'vulnerable',
               'badge': 'Сырые ПДн в скриптах'},
              {'type': 'process',
               'id': '6.3',
               'title': 'Отправка отчетов по почте',
               'subtitle': 'P&L, ABC-анализ в Excel\n'
                           'рассылаются через незащищенный\n'
                           'Exchange Mail Server',
               'status': 'vulnerable',
               'badge': 'Почтовая утечка'},
              {'type': 'store',
               'id': 'D1',
               'title': 'Файловый сервер клиники',
               'subtitle': 'Папки: Pacients, Journals, Registry\n'
                           'Сырые файлы клиники за все годы\n'
                           'Доступны аналитику без ограничений',
               'status': 'vulnerable',
               'badge': 'Нет Data Lineage'},
              {'type': 'store',
               'id': 'D2',
               'title': 'Локальный диск ноутбука аналитика',
               'subtitle': 'Неконтролируемая теневая копия базы\n'
                           'Нет шифрования диска, нет DLP контроля,\n'
                           'риск выноса базы за пределы офиса',
               'status': 'vulnerable',
               'badge': 'Критическая утечка'}],
 'flows': [{'label': 'Запуск скрипта копирования файлов',
            'style': 'normal',
            'source': 'E1',
            'target': '6.1'},
           {'label': 'Выгрузка сырых Excel по SMB',
            'style': 'vulnerable',
            'source': 'D1',
            'target': '6.1'},
           {'label': 'Парсинг pandas DataFrame', 'style': 'normal', 'source': '6.1', 'target': '6.2'},
           {'label': 'Кэширование CSV на диск ПК',
            'style': 'vulnerable',
            'source': '6.2',
            'target': 'D2'},
           {'label': 'Генерация отчета P&L, ABC', 'style': 'normal', 'source': '6.2', 'target': '6.3'},
           {'label': 'Отправка отчетов руководству по почте',
            'style': 'vulnerable',
            'source': '6.3',
            'target': 'E2'}]}

p6_to_be = {'title': 'DFD Процесс 6 (To-Be): Контур обезличенной аналитики (Data Lakehouse & Privacy Gateway)',
 'subtitle': 'Целевое состояние: Privacy Gateway (k-anonymity), ClickHouse Data Lake, Apache Superset, '
             'исключение PII из аналитики',
 'elements': [{'type': 'entity',
               'id': 'E1',
               'title': 'Бизнес-аналитик (BA)',
               'subtitle': 'Доступ через Web BI\nБез права скачивания сырых ПДн'},
              {'type': 'entity',
               'id': 'E2',
               'title': 'ML / AI инженеры',
               'subtitle': 'Обучение моделей LLM/ML\nТОЛЬКО на обезличенных сетах'},
              {'type': 'entity',
               'id': 'E3',
               'title': 'Руководство клиники',
               'subtitle': 'Дашборды в BI Superset\nМетрики в реальном времени'},
              {'type': 'process',
               'id': '6.1',
               'title': 'CDC & ETL Экстракция',
               'subtitle': 'Debezium + Kafka Connect\n'
                           'Потоковое извлечение изменений\n'
                           'из PostgreSQL (OLTP)',
               'status': 'secure',
               'badge': 'CDC Streaming'},
              {'type': 'process',
               'id': '6.2',
               'title': 'Privacy & Anonymization Engine',
               'subtitle': 'Удаление прямых идентификаторов\n'
                           'К-анонимизация (возрастные группы)\n'
                           'Дифференциальная приватность',
               'status': 'secure',
               'badge': 'Роскомнадзор 996'},
              {'type': 'process',
               'id': '6.3',
               'title': 'Витрины данных и BI',
               'subtitle': 'Агрегаты в ClickHouse (OLAP)\n'
                           'Дашборды в Apache Superset\n'
                           'Тег: ANALYTICS_ANONYMIZED',
               'status': 'secure',
               'badge': 'Zero Raw PII'},
              {'type': 'store',
               'id': 'D1',
               'title': 'Operational DBs (OLTP)',
               'subtitle': 'Patient, Appointment, EHR DBs\n'
                           'Закрытый производственный контур\n'
                           'Прямой доступ аналитика ЗАПРЕЩЕН',
               'status': 'secure',
               'badge': 'Strict Isolation'},
              {'type': 'store',
               'id': 'D2',
               'title': 'Analytical Lake (ClickHouse)',
               'subtitle': 'Колоночная СУБД для аналитики\n'
                           '100% обезличенные данные!\n'
                           'Агрегаты выручки, нагрузки, услуг',
               'status': 'secure',
               'badge': 'ClickHouse OLAP'},
              {'type': 'store',
               'id': 'D3',
               'title': 'Data Catalog (OpenMetadata)',
               'subtitle': 'Единый каталог метаданных\n'
                           'Сквозной Data Lineage от OLTP к BI\n'
                           'Политики маскирования и теги',
               'status': 'secure',
               'badge': 'Data Lineage'},
              {'type': 'security_badge',
               'id': 'SEC1',
               'title': 'Принципы защиты',
               'subtitle': '• Аналитик и AI физически\n'
                           '  НЕ ИМЕЮТ доступа к ПДн\n'
                           '• Никаких файлов на ноутбуках\n'
                           '• К-анонимизация и обобщение\n'
                           '• Сквозной Data Lineage\n'
                           '• Готовность к 5-кратному росту\n'
                           '  и обучению LLM/ML'}],
 'flows': [{'label': 'CDC поток изменений (Debezium)',
            'style': 'secure',
            'source': 'D1',
            'target': '6.1'},
           {'label': 'Потоковая передача в Privacy Engine',
            'style': 'secure',
            'source': '6.1',
            'target': '6.2'},
           {'label': 'Загрузка обезличенных данных', 'style': 'secure', 'source': '6.2', 'target': 'D2'},
           {'label': 'Построение витрин отчетности',
            'style': 'secure',
            'source': '6.2',
            'target': '6.3'},
           {'label': 'Регистрация связей в Data Lineage',
            'style': 'secure',
            'source': '6.3',
            'target': 'D3'},
           {'label': 'Аналитик открывает BI Superset (Web)',
            'style': 'secure',
            'source': 'E1',
            'target': '6.3'},
           {'label': 'ML обучение на ClickHouse витринах',
            'style': 'secure',
            'source': 'E2',
            'target': 'D2'},
           {'label': 'Дашборды руководству в браузере',
            'style': 'secure',
            'source': '6.3',
            'target': 'E3'}]}

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
    ('dfd-p6-analytics-to-be', p6_to_be),
]


def main():
    DIAGRAMS_DIR.mkdir(exist_ok=True)
    for name, diagram in all_diagrams:
        path = DIAGRAMS_DIR / f"{name}.svg"
        path.write_text(render_svg(diagram), encoding="utf-8")
        print(f"Generated: {path.name}")


if __name__ == "__main__":
    main()
