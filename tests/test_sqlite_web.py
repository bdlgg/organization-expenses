"""Проверки сохранности исходной SQLite-базы предыдущей ПР7."""

import sqlite3

from db.database import DB_PATH, get_connection


def test_pr7_source_database_is_preserved():
    assert DB_PATH.exists()

    with sqlite3.connect(DB_PATH) as connection:
        counts = {
            table: connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            for table in (
                "categories",
                "departments",
                "documents",
                "expenses",
            )
        }

    assert counts == {
        "categories": 2,
        "departments": 3,
        "documents": 3,
        "expenses": 3,
    }


def test_source_database_connection_enables_foreign_keys():
    connection = get_connection()
    try:
        result = connection.execute("PRAGMA foreign_keys").fetchone()
    finally:
        connection.close()

    assert result == (1,)
