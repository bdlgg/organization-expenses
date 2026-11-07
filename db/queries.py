"""Загрузка именованных SQL-запросов из sql/queries.sql."""

import re

from db.database import BASE_DIR

QUERIES_PATH = BASE_DIR / "sql" / "queries.sql"
QUERY_HEADER = re.compile(r"(?m)^--\s*(\d+)\.\s*.*$")


def load_sql_queries() -> dict[int, str]:
    """Загрузить запросы, разделённые комментариями с их номерами."""
    content = QUERIES_PATH.read_text(encoding="utf-8")
    sections = re.split(QUERY_HEADER, content)
    queries = {}

    for index in range(1, len(sections), 2):
        number = int(sections[index])
        query = sections[index + 1].strip()
        query = query.rstrip(";").strip()

        if not query:
            raise ValueError(f"SQL-запрос №{number} пустой")
        if number in queries:
            raise ValueError(f"Номер SQL-запроса №{number} повторяется")

        queries[number] = query

    if not queries:
        raise ValueError(f"В файле {QUERIES_PATH} не найдены SQL-запросы")

    return queries


SQL_QUERIES = load_sql_queries()
