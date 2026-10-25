"""Создание таблиц отдельной SQLite-базы проекта."""

from db.database import DB_PATH, initialize_database


def main() -> None:
    initialize_database()
    print(f"Структура SQLite создана: {DB_PATH}")


if __name__ == "__main__":
    main()
