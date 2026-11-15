"""Перенос исходных JSON-данных проекта в реляционную SQLite-базу."""

import json
import sqlite3
from pathlib import Path
from typing import Any

from db.database import BASE_DIR, DB_PATH, get_connection, initialize_database

DATA_DIR = BASE_DIR / "data"
CATEGORIES_FILE = DATA_DIR / "categories.json"
DEPARTMENTS_FILE = DATA_DIR / "departments.json"
DOCUMENTS_FILE = DATA_DIR / "documents.json"
EXPENSES_FILE = DATA_DIR / "expenses.json"


def load_json(path: Path) -> list[dict[str, Any]]:
    """Прочитать список объектов из JSON-файла."""
    if not path.exists():
        raise FileNotFoundError(f"Не найден исходный файл: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"Ожидался список объектов в файле {path.name}")
    if not all(isinstance(item, dict) for item in data):
        raise ValueError(f"В файле {path.name} есть некорректные записи")
    return data


def _import_reference_data(
    connection: sqlite3.Connection,
    categories: list[dict[str, Any]],
    departments: list[dict[str, Any]],
    documents: list[dict[str, Any]],
) -> None:
    """Перенести справочники и сформировать отображение значений в ID."""
    connection.executemany(
        "INSERT INTO categories (name) VALUES (?)",
        [(item["name"].strip(),) for item in categories],
    )
    connection.executemany(
        "INSERT INTO departments (name) VALUES (?)",
        [(item["name"].strip(),) for item in departments],
    )
    connection.executemany(
        "INSERT INTO documents (number) VALUES (?)",
        [(item["number"].strip(),) for item in documents],
    )


def _import_expenses(
    connection: sqlite3.Connection,
    expenses: list[dict[str, Any]],
) -> None:
    """Перенести расходы, заменив текстовые значения на внешние ключи."""
    category_ids = {
        row["name"]: row["id"]
        for row in connection.execute("SELECT id, name FROM categories")
    }
    department_ids = {
        row["name"]: row["id"]
        for row in connection.execute("SELECT id, name FROM departments")
    }
    document_ids = {
        row["number"]: row["id"]
        for row in connection.execute("SELECT id, number FROM documents")
    }

    rows = []
    for expense in expenses:
        try:
            amount = float(expense["amount"])
            category_id = category_ids[expense["category"]]
            department_id = department_ids[expense["department"]]
            document_id = document_ids[expense["document"]]
        except KeyError as error:
            raise ValueError(
                "Расход ссылается на отсутствующую запись справочника: "
                f"{error.args[0]}"
            ) from error
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Некорректная сумма у расхода {expense.get('id', '?')}"
            ) from error

        rows.append(
            (
                int(expense["id"]),
                amount,
                category_id,
                department_id,
                document_id,
            )
        )

    connection.executemany(
        """
        INSERT INTO expenses (
            id, amount, category_id, department_id, document_id
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        rows,
    )


def import_data() -> None:
    """Заменить данные SQLite актуальным содержимым JSON-файлов."""
    initialize_database()

    categories = load_json(CATEGORIES_FILE)
    departments = load_json(DEPARTMENTS_FILE)
    documents = load_json(DOCUMENTS_FILE)
    expenses = load_json(EXPENSES_FILE)

    connection = get_connection()
    connection.row_factory = sqlite3.Row
    try:
        # Удаляем записи в порядке, соблюдающем внешние ключи.
        connection.execute("DELETE FROM expenses")
        connection.execute("DELETE FROM documents")
        connection.execute("DELETE FROM departments")
        connection.execute("DELETE FROM categories")

        _import_reference_data(
            connection,
            categories,
            departments,
            documents,
        )
        _import_expenses(connection, expenses)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def main() -> None:
    import_data()
    print(f"JSON-данные перенесены в SQLite: {DB_PATH}")


if __name__ == "__main__":
    main()
