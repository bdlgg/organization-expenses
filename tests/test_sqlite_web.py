"""Проверки импорта SQLite и пользовательских страниц проекта ПР7."""

import sqlite3

from django.test import Client

from db.database import DB_PATH, get_connection


def test_sqlite_database_contains_imported_data():
    assert DB_PATH.exists()

    connection = get_connection()
    try:
        connection.row_factory = sqlite3.Row
        counts = {
            table: connection.execute(
                f"SELECT COUNT(*) AS amount FROM {table}"
            ).fetchone()["amount"]
            for table in (
                "categories",
                "departments",
                "documents",
                "expenses",
            )
        }
    finally:
        connection.close()

    assert counts["categories"] == 2
    assert counts["departments"] == 3
    assert counts["documents"] == 3
    assert counts["expenses"] == 3


def test_foreign_key_checks_are_enabled():
    connection = get_connection()
    try:
        result = connection.execute("PRAGMA foreign_keys").fetchone()
    finally:
        connection.close()

    assert result == (1,)


def test_expense_list_page_displays_sqlite_data():
    response = Client().get("/expenses/", HTTP_HOST="localhost")

    assert response.status_code == 200
    assert "Оборудование" in response.content.decode("utf-8")
    assert "Счет №101" in response.content.decode("utf-8")


def test_expense_filter_uses_minimum_amount():
    response = Client().get(
        "/expenses/?min_amount=20000",
        HTTP_HOST="localhost",
    )
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "25000,00" in content
    assert 'href="/expenses/3/"' in content
    assert 'href="/expenses/1/"' not in content
    assert 'href="/expenses/2/"' not in content


def test_expense_detail_page_displays_related_data():
    response = Client().get("/expenses/1/", HTTP_HOST="localhost")
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "Оборудование" in content
    assert "IT" in content
    assert "Счет №101" in content


def test_statistics_page_displays_aggregates_and_groups():
    response = Client().get(
        "/expenses/statistics/?threshold=10000",
        HTTP_HOST="localhost",
    )
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "Статистика расходов" in content
    assert "Расходы по категориям" in content
    assert "Расходы по подразделениям" in content
    assert "Оборудование" in content


def test_catalog_pages_display_data_from_sqlite():
    client = Client()
    paths = (
        "/categories/",
        "/departments/",
        "/documents/",
    )

    for path in paths:
        response = client.get(path, HTTP_HOST="localhost")
        assert response.status_code == 200


def test_missing_expense_returns_404():
    response = Client().get("/expenses/999/", HTTP_HOST="localhost")

    assert response.status_code == 404
    assert "Расход не найден" in response.content.decode("utf-8")
