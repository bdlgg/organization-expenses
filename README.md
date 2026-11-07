# Система учёта расходов организации

Учебный проект на Python: консольная версия для предыдущих практических работ
и веб-интерфейс на Django. В рамках ПР7 добавлен отдельный слой реляционного
хранения данных SQLite. Django ORM в этой работе не используется: запросы к
новой базе выполняются стандартной библиотекой `sqlite3`.

## Функциональность

- просмотр списка расходов и карточки отдельного расхода;
- поиск по категории, подразделению и номеру документа;
- фильтрация по минимальной сумме, категории и подразделению;
- сортировка списка расходов;
- сводные показатели: сумма, среднее, минимум, максимум и число расходов;
- статистика по категориям и подразделениям, фильтрация групп через `HAVING`;
- справочники категорий, подразделений и документов с агрегатами по расходам;
- исходная консольная программа `main.py` и JSON-хранилище предыдущих этапов.

## Стек и версия Python

- **Python 3.12.x** (исходное виртуальное окружение было создано на Python 3.12.13);
- Django 5.2;
- SQLite и стандартная библиотека `sqlite3`;
- pytest и flake8.

Виртуальное окружение (`.venv`) не хранится в репозитории: оно привязано
к пути и интерпретатору компьютера, на котором было создано. Создайте его
в корне проекта или активируйте собственное окружение Python 3.12.x.

## Структура базы данных

Файл базы данных: `data/organization_expenses.sqlite`.

| Таблица | Поля | Связи |
| --- | --- | --- |
| `categories` | `id INTEGER PRIMARY KEY`, `name TEXT UNIQUE NOT NULL` | Справочник категорий |
| `departments` | `id INTEGER PRIMARY KEY`, `name TEXT UNIQUE NOT NULL` | Справочник подразделений |
| `documents` | `id INTEGER PRIMARY KEY`, `number TEXT UNIQUE NOT NULL` | Справочник документов |
| `expenses` | `id INTEGER PRIMARY KEY`, `amount REAL NOT NULL`, `category_id INTEGER`, `department_id INTEGER`, `document_id INTEGER` | Внешние ключи на три справочника |

`expenses.category_id` ссылается на `categories.id`, `expenses.department_id` —
на `departments.id`, а `expenses.document_id` — на `documents.id`. Сумма не
может быть отрицательной. Для ускорения выборок добавлены индексы по сумме и
внешним ключам.

Схема создаётся SQL-командами из `sql/schema.sql`. Подключение настраивается в
`db/database.py`; скрипт `db/import_json.py` переносит данные из четырёх JSON-
файлов, преобразуя значения категорий, подразделений и документов во внешние
ключи. JSON сохранён для консольной версии и как исходный материал для импорта.

`sql/queries.sql` содержит 17 пронумерованных запросов: выборки списков,
фильтрацию `WHERE`, соединения `JOIN`, агрегаты `COUNT`, `SUM`, `AVG`, `MIN`,
`MAX`, группировку `GROUP BY`, фильтрацию групп `HAVING` и `LEFT JOIN`.
Загрузка и нумерация запросов выполняется модулем `db/queries.py`. Django-
представления используют запросы из этого файла; динамические значения
передаются отдельными параметрами `?`, а `sqlite3.Row` обеспечивает доступ
к полям результата по именам. Результаты передаются в HTML-шаблоны через
контекст.

## Страницы сайта

| Адрес | Назначение |
| --- | --- |
| `/` | Главная страница и общая сводка из SQLite |
| `/expenses/` | Список, поиск, фильтрация и сортировка расходов |
| `/expenses/1/` | Карточка расхода с названием категории, подразделения и документа |
| `/expenses/statistics/` | Агрегаты, статистика по категориям и подразделениям, фильтрация групп `HAVING` |
| `/categories/` | Категории, связанные суммы и категории без расходов |
| `/departments/` | Подразделения и связанные с ними суммы |
| `/documents/` | Документы и связанные с ними суммы |

## Запуск на macOS / Linux

Откройте терминал в корне папки `organization-expenses`.

1. Проверьте Python:

   ```bash
   python3.12 --version
   ```

2. Активируйте существующее окружение, если оно создано на Python 3.12:

   ```bash
   source .venv/bin/activate
   python --version
   ```

   Если `.venv` отсутствует или использует другую версию Python, создайте его:

   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

3. Установите зависимости:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. Создайте структуру SQLite и перенесите исходные данные:

   ```bash
   python -m db.init_db
   python -m db.import_json
   ```

   Повторный импорт допустим: таблицы заполняются актуальными данными из JSON.
   Файл `data/organization_expenses.sqlite` будет создан автоматически.

5. Проверьте проект и запустите сервер:

   ```bash
   python manage.py check
   pytest -v
   flake8 . --extend-exclude=venv
   python manage.py runserver
   ```

6. Откройте в браузере `http://127.0.0.1:8000/`.

## Запуск в Windows PowerShell

Из корня проекта:

```powershell
py -3.12 --version
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m db.init_db
python -m db.import_json
python manage.py check
pytest -v
flake8 . --extend-exclude=venv
python manage.py runserver
```

Если виртуальное окружение уже работает под Python 3.12, повторно создавать его
не нужно — активируйте его и продолжайте с установки зависимостей.

## Команды SQLite для проверки

Для интерактивного просмотра базы, если установлен SQLite CLI:

```bash
sqlite3 data/organization_expenses.sqlite
.headers on
.mode column
.tables
.schema expenses
SELECT * FROM expenses;
.parameter init
.parameter set ?1 10000
.read sql/queries.sql
.quit
```

Перед выполнением файла запросов задаётся значение `10000` для параметра `?`,
который используется в запросах №13 и №14. Все запросы также автоматически
проверяются тестом `test_all_documented_queries_execute_against_project_database`.

Можно открыть `data/organization_expenses.sqlite` в расширении SQLite Viewer
для VS Code или в другом просмотрщике SQLite. SQL-запросы для демонстрации
сохранены в `sql/queries.sql`.

## Консольная версия

Предыдущая версия проекта по-прежнему запускается отдельно:

```bash
python main.py
```

Она продолжает использовать JSON-файлы; веб-интерфейс ПР7 читает данные из
`data/organization_expenses.sqlite`.

## Текущий этап разработки

В рамках ПР7 добавлены схема SQLite, импорт данных из JSON, 17 SQL-запросов,
единый загрузчик SQL из `sql/queries.sql`, отображение данных через Django views
и шаблоны, параметризованные фильтры и статистика по категориям и подразделениям.
Справочники и главная страница также получают данные через запросы из SQL-файла.
Структура SQLite подключена независимо от Django ORM, как предписано практической
работой. Предыдущая консольная версия, JSON-хранилище и объектная модель сохранены.
