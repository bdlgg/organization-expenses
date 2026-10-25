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

- **Python 3.11.x** (исходное виртуальное окружение в переданном архиве было
  создано на Python 3.11.17);
- Django 5.2;
- SQLite и стандартная библиотека `sqlite3`;
- pytest и flake8.

Виртуальное окружение (`.venv`) не включено в архив результата: оно привязано
к пути и интерпретатору компьютера, на котором было создано. Создайте его в
корне проекта или используйте уже имеющееся, если команда `python --version`
показывает Python 3.11.x.

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

`sql/queries.sql` содержит 15 документированных запросов: списки, фильтрацию
`WHERE`, соединения `JOIN`, агрегаты `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`,
группировку `GROUP BY`, фильтрацию групп `HAVING` и `LEFT JOIN`. В Django-
представлениях пользовательские значения передаются параметрами `?`, а строки
результата читаются через `sqlite3.Row` и передаются в HTML-шаблоны через
контекст.

## Страницы сайта

| Адрес | Назначение |
| --- | --- |
| `/` | Главная страница и общая сводка из SQLite |
| `/expenses/` | Список, поиск, фильтрация и сортировка расходов |
| `/expenses/1/` | Карточка расхода с названием категории, подразделения и документа |
| `/expenses/statistics/` | Агрегаты, статистика по категориям и подразделениям, `HAVING` |
| `/categories/` | Категории и связанные с ними суммы |
| `/departments/` | Подразделения и связанные с ними суммы |
| `/documents/` | Документы и связанные с ними суммы |

## Запуск на macOS / Linux

Откройте терминал в корне папки `organization-expenses`.

1. Проверьте Python:

   ```bash
   python3.11 --version
   ```

2. Активируйте существующее окружение, если оно создано на Python 3.11:

   ```bash
   source .venv/bin/activate
   python --version
   ```

   Если `.venv` отсутствует или использует другую версию Python, создайте его:

   ```bash
   python3.11 -m venv .venv
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
py -3.11 --version
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m db.init_db
python -m db.import_json
python manage.py check
pytest -v
flake8 . --extend-exclude=venv
python manage.py runserver
```

Если виртуальное окружение уже работает под Python 3.11, повторно создавать его
не нужно — активируйте его и продолжайте с установки зависимостей.

## Команды SQLite для проверки

Для интерактивного просмотра базы, если установлен SQLite CLI:

```bash
sqlite3 data/organization_expenses.sqlite
.tables
.schema expenses
SELECT * FROM expenses;
.exit
```

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

В рамках ПР7 добавлены схема SQLite, импорт данных из JSON, 15 SQL-запросов,
отображение данных через Django views и шаблоны, параметризованный поиск и
страница статистики. Структура базы подключена независимо от Django ORM, как
предписано практической работой. Изменения зафиксированы отдельным Git-коммитом
с префиксом `PR7:`.
