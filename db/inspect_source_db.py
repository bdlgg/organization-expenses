"""Проверка структуры исходной SQLite-базы ПР7 без изменения данных."""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DB = BASE_DIR / "data" / "organization_expenses.sqlite"


def main() -> None:
    """Вывести пользовательские таблицы, поля и число записей."""
    if not SOURCE_DB.exists():
        raise FileNotFoundError(
            f"Исходная база не найдена: {SOURCE_DB}"
        )

    with sqlite3.connect(SOURCE_DB) as connection:
        connection.row_factory = sqlite3.Row
        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        for table_row in tables:
            table_name = table_row["name"]
            print(f"\nТаблица: {table_name}")

            # Имя таблицы получено из sqlite_master, а не от пользователя.
            escaped_name = table_name.replace('"', '""')
            columns = connection.execute(
                f'PRAGMA table_info("{escaped_name}")'
            ).fetchall()

            for column in columns:
                print(
                    f"  {column['name']}: {column['type']}; "
                    f"NOT NULL={bool(column['notnull'])}; "
                    f"PRIMARY KEY={bool(column['pk'])}"
                )

            count = connection.execute(
                f'SELECT COUNT(*) FROM "{escaped_name}"'
            ).fetchone()[0]
            print(f"Записей: {count}")


if __name__ == "__main__":
    main()
