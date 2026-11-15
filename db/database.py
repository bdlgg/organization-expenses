"""Подключение к SQLite-базе данных проекта."""

import sqlite3
from contextlib import closing
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "organization_expenses.sqlite"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"


def get_connection() -> sqlite3.Connection:
    """Открыть соединение и включить проверку внешних ключей."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    """Создать таблицы и индексы по SQL-схеме проекта."""
    with closing(get_connection()) as connection:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        connection.executescript(schema)
        connection.commit()
