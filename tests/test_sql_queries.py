"""Проверка SQL-запросов, хранящихся в sql/queries.sql."""

import re

from db.database import get_connection
from db.queries import SQL_QUERIES


def test_sql_file_contains_at_least_ten_numbered_queries():
    assert len(SQL_QUERIES) >= 10
    assert set(SQL_QUERIES) == set(range(1, 18))


def test_all_documented_queries_execute_against_project_database():
    connection = get_connection()
    try:
        for number, query in SQL_QUERIES.items():
            parameters = (10000,) if number in {13, 14} else ()
            connection.execute(query, parameters).fetchall()
    finally:
        connection.close()


def test_threshold_queries_use_parameters():
    assert "HAVING SUM(e.amount) > ?" in SQL_QUERIES[13]
    assert "HAVING SUM(e.amount) >= ?" in SQL_QUERIES[14]


def test_sql_file_covers_required_query_types():
    query_texts = [query.upper() for query in SQL_QUERIES.values()]

    where_queries = sum("WHERE" in query for query in query_texts)
    join_queries = sum(
        bool(re.search(r"\bJOIN\b", query)) for query in query_texts
    )
    aggregate_queries = sum(
        bool(re.search(r"\b(COUNT|SUM|AVG|MIN|MAX)\s*\(", query))
        for query in query_texts
    )
    group_by_queries = sum("GROUP BY" in query for query in query_texts)

    assert where_queries >= 2
    assert join_queries >= 2
    assert aggregate_queries >= 2
    assert group_by_queries >= 2
