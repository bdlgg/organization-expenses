# Система учёта расходов организации

Учебный Django-проект для ведения реестра расходов организации. Веб-приложение
работает с данными через Django ORM; консольная версия и материалы предыдущих
практических работ сохранены.

## Функциональность

- главная страница со сводными показателями;
- список расходов с поиском по категории, подразделению и документу;
- фильтрация по сумме, категории, подразделению, статусу и диапазону дат;
- сортировка по сумме, дате, категории и подразделению;
- пагинация с сохранением заданных фильтров;
- подробная карточка расхода по уникальному человекочитаемому URL (`slug`);
- статусы расхода: «Ожидает обработки», «Одобрен», «Оплачен», «Отменён»;
- статистика с учётом статусов: отменённые записи остаются в журнале, но не
  включаются в фактические суммы;
- группировка расходов по категориям и подразделениям;
- вычисляемый базой данных признак крупного расхода (сумма от 10 000 ₽);
- административная панель со справочниками и расходами;
- поиск и фильтрация в Django Admin, быстрые изменения, массовые действия;
- просмотр связанных расходов во встроенных таблицах карточек справочников;
- Django Debug Toolbar для локального анализа SQL-запросов;
- контекстный процессор с общим названием сайта и количеством записей;
- исходная консольная программа `main.py` и JSON-хранилище предыдущих этапов.

## Технологии

- Python 3.12;
- Django 5.2;
- SQLite;
- Django ORM;
- Django Debug Toolbar;
- Unidecode для транслитерации адресов;
- pytest и flake8.

## Модели и связи

| Модель | Поля | Назначение и связи |
| --- | --- | --- |
| `Category` | `id`, `name` | Справочник категорий; одна категория связана со многими расходами |
| `Department` | `id`, `name` | Справочник подразделений; одно подразделение связано со многими расходами |
| `Document` | `id`, `number` | Подтверждающий документ; один документ может быть связан с несколькими расходами |
| `Expense` | `id`, `amount`, `expense_date`, `status`, `slug`, `is_large`, `category`, `department`, `document` | Запись расхода с датой, статусом, вычисляемым признаком и тремя внешними ключами |

`Expense.category`, `Expense.department` и `Expense.document` используют
`ForeignKey(on_delete=PROTECT, related_name="expenses")`. Удаление справочника,
на который ссылается расход, блокируется, чтобы не потерять историю учёта.
Отмена расхода меняет статус на «Отменён», а не удаляет строку из базы данных.

`Expense.Status` — перечисление `TextChoices`. Для выборок предусмотрены методы
`Expense.objects.pending()`, `.approved()`, `.paid()`, `.cancelled()`,
`.not_cancelled()`, `.for_date()`, `.for_period()` и `.above_amount()`.

Поле `is_large` — `GeneratedField`: SQLite вычисляет его непосредственно на
уровне базы по условию `amount >= 10000.00`. В административной панели значение
доступно только для чтения.

## Django Admin

Административная панель доступна по адресу `http://127.0.0.1:8000/admin/`.
Модели `Category`, `Department`, `Document` и `Expense` зарегистрированы с
настройками `ModelAdmin`:

- столбцы, сортировка, фильтры и постраничный вывод;
- поиск по собственным и связанным полям;
- редактирование суммы и статуса в списке расходов;
- автодополнение для полей категории, подразделения и документа;
- переход к записям по дате;
- массовые действия: отметить оплаченные, отменить, вернуть в обработку;
- встроенные таблицы связанных расходов в карточках категорий,
  подразделений и документов.

Для входа создайте административную учётную запись командой
`python manage.py createsuperuser`. Суперпользователь Django — отдельная учётная
запись административной панели, а не модель предметной области.

## Django ORM и SQL

Представления используют `filter()`, `exclude()`, `Q`, `order_by()`,
`get_object_or_404()`, `select_related()`, `annotate()`, `aggregate()`, `F()`,
`values()` и `Paginator`. Списки сортируются и фильтруются на стороне базы данных,
а связанные справочники расходов загружаются через `select_related()`.

В Django Shell можно посмотреть SQL сформированного набора:

```python
from expenses.models import Expense

queryset = Expense.objects.select_related(
    "category", "department", "document"
).filter(status=Expense.Status.PAID).order_by("-expense_date")

print(queryset.query)
print(queryset.explain())
```

Для подсчёта фактически выполненных запросов используйте
`CaptureQueriesContext` из `django.test.utils`. Django Debug Toolbar выводит SQL
на страницах приложения при локальной разработке, если пакет установлен и
`DEBUG=True`.

## Даты и статусы старых записей

В исходной базе ПР7 у расходов отсутствовали дата операции и статус. Поэтому
миграция ПР10 оставляет дату существующих записей пустой, а статус устанавливает
в «Ожидает обработки». Это не выдаёт сегодняшнюю дату за историческую.
Новые расходы по умолчанию получают текущую локальную дату и статус
«Ожидает обработки». В карточке старой записи пустая дата отображается как
«Не указана в исходных данных».

## URL расходов

Каноническая карточка расхода открывается по адресу вида
`/expenses/raskhod-oborudovanie-it-1/`. Метод `get_absolute_url()` формирует этот
адрес. Старые числовые адреса `/expenses/1/` сохранены: они перенаправляют на
соответствующий URL по `slug`.

## Базы данных и перенос данных

В проекте используются две SQLite-базы с разными назначениями:

- `data/organization_expenses.sqlite` — исходная база предыдущего этапа ПР7;
- `db.sqlite3` — целевая база, управляемая Django ORM.

Скрипт `db/import_sqlite_to_orm.py` переносит справочники до расходов,
сохраняет первичные ключи и связи, проверяет внешние ключи и выполняет операции
в транзакции. При повторном запуске обновляются исходные поля из ПР7, при этом
добавленные в ПР10 дата и статус существующих расходов сохраняются.

`sql/schema.sql`, `sql/queries.sql`, `db/database.py` и `db/queries.py` оставлены
как материалы ПР7. Веб-представления используют Django ORM и не выполняют
прямые SQL-запросы.

## Структура проекта

```text
organization-expenses/
├── catalogs/                 # Category, Department, Document, admin и views
├── expenses/                 # Expense, менеджер, admin и views
│   └── migrations/           # Миграции полей, slug и GeneratedField
├── homepage/                 # Главная страница и общий context processor
├── org_expenses/             # Настройки и корневые URL Django
├── db/                       # Инструменты исходной БД и перенос в ORM
├── data/                     # JSON-файлы и исходная база ПР7
├── docs/                     # Контрольные списки практических работ
├── models/                   # Объектная модель консольной версии
├── sql/                      # SQL-схема и запросы предыдущей ПР7
├── tests/                    # Автоматизированные тесты
├── manage.py
├── main.py                   # Консольная версия
└── README.md
```

## Запуск на macOS / Linux

Из корневой папки проекта:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py migrate
python db/inspect_source_db.py
python db/import_sqlite_to_orm.py
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
pytest -v
flake8 . --extend-exclude=venv,.venv
python manage.py createsuperuser
python manage.py runserver
```

Откройте `http://127.0.0.1:8000/`. Django Admin доступна по адресу
`http://127.0.0.1:8000/admin/`. При установленном `django-debug-toolbar` панель
отладки появляется на локальных страницах.

Чтобы отключить Debug Toolbar, задайте `DJANGO_DEBUG=False`. В производственной
среде обязательно задайте собственный секретный ключ через `DJANGO_SECRET_KEY`
и отключите режим отладки.

## Запуск в Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py migrate
python db/inspect_source_db.py
python db/import_sqlite_to_orm.py
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
pytest -v
flake8 . --extend-exclude=venv,.venv
python manage.py createsuperuser
python manage.py runserver
```

## Контроль выполнения практических работ

- [ПР9 — переход на Django ORM](docs/PR9_CHECKLIST.md)
- [ПР10 — административная панель и углублённая работа с ORM](docs/PR10_CHECKLIST.md)

## Консольная версия

Предыдущая консольная версия запускается отдельно и по-прежнему использует
JSON-файлы:

```bash
python main.py
```

## Автор

Укажите ФИО и учебную группу перед сдачей проекта.
