"""Перенос данных ПР7 из SQLite в таблицы, управляемые Django ORM."""

import os
import sqlite3
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

import django
from django.db import transaction

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DB = BASE_DIR / "data" / "organization_expenses.sqlite"
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "org_expenses.settings",
)
django.setup()

# Импорт моделей выполняется после инициализации Django.
from catalogs.models import Category, Department, Document  # noqa: E402
from expenses.models import Expense  # noqa: E402


REQUIRED_TABLES = {
    "categories",
    "departments",
    "documents",
    "expenses",
}


def _read_source_data() -> dict[str, list[sqlite3.Row]]:
    """Прочитать справочники и расходы из исходной базы ПР7."""
    if not SOURCE_DB.exists():
        raise FileNotFoundError(
            f"Исходная база не найдена: {SOURCE_DB}"
        )

    with sqlite3.connect(SOURCE_DB) as connection:
        connection.row_factory = sqlite3.Row
        existing_tables = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        }
        missing_tables = REQUIRED_TABLES - existing_tables
        if missing_tables:
            names = ", ".join(sorted(missing_tables))
            raise RuntimeError(
                f"В исходной базе отсутствуют таблицы: {names}"
            )

        return {
            table_name: connection.execute(
                f"SELECT * FROM {table_name} ORDER BY id"
            ).fetchall()
            for table_name in sorted(REQUIRED_TABLES)
        }


def _validate_relationships(
    source_data: dict[str, list[sqlite3.Row]],
) -> None:
    """Убедиться, что каждый расход ссылается на существующие справочники."""
    category_ids = {row["id"] for row in source_data["categories"]}
    department_ids = {row["id"] for row in source_data["departments"]}
    document_ids = {row["id"] for row in source_data["documents"]}

    for expense in source_data["expenses"]:
        if expense["category_id"] not in category_ids:
            raise ValueError(
                f"Расход {expense['id']} ссылается на отсутствующую "
                f"категорию {expense['category_id']}"
            )
        if expense["department_id"] not in department_ids:
            raise ValueError(
                f"Расход {expense['id']} ссылается на отсутствующее "
                f"подразделение {expense['department_id']}"
            )
        if expense["document_id"] not in document_ids:
            raise ValueError(
                f"Расход {expense['id']} ссылается на отсутствующий "
                f"документ {expense['document_id']}"
            )


def import_data() -> None:
    """Перенести данные, сохранив исходные ID и связи между таблицами."""
    source_data = _read_source_data()
    _validate_relationships(source_data)

    try:
        with transaction.atomic():
            # Сначала справочники: на них ссылаются записи Expense.
            for row in source_data["categories"]:
                Category.objects.update_or_create(
                    pk=row["id"],
                    defaults={"name": row["name"]},
                )

            for row in source_data["departments"]:
                Department.objects.update_or_create(
                    pk=row["id"],
                    defaults={"name": row["name"]},
                )

            for row in source_data["documents"]:
                Document.objects.update_or_create(
                    pk=row["id"],
                    defaults={"number": row["number"]},
                )

            # Только после справочников переносим расходы и их ForeignKey.
            for row in source_data["expenses"]:
                try:
                    amount = Decimal(str(row["amount"]))
                except (InvalidOperation, TypeError, ValueError) as error:
                    raise ValueError(
                        f"Некорректная сумма расхода {row['id']}"
                    ) from error

                if not amount.is_finite() or amount < 0:
                    raise ValueError(
                        f"Недопустимая сумма расхода {row['id']}"
                    )

                Expense.objects.update_or_create(
                    pk=row["id"],
                    defaults={
                        "amount": amount,
                        "category_id": row["category_id"],
                        "department_id": row["department_id"],
                        "document_id": row["document_id"],
                    },
                )
    except Exception:
        # transaction.atomic() автоматически откатывает все операции.
        raise

    print("Перенос данных завершён.")
    print(f"Категорий: {Category.objects.count()}")
    print(f"Подразделений: {Department.objects.count()}")
    print(f"Документов: {Document.objects.count()}")
    print(f"Расходов: {Expense.objects.count()}")
    print(f"Источник: {SOURCE_DB}")


def main() -> None:
    import_data()


if __name__ == "__main__":
    main()
