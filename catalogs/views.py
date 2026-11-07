"""Представления справочников, данные которых хранятся в SQLite."""

import sqlite3
from contextlib import closing

from django.shortcuts import render

from db.database import get_connection
from db.queries import SQL_QUERIES


def _open_row_connection() -> sqlite3.Connection:
    """Открыть соединение SQLite с доступом к полям по именам."""
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    return connection


def categories_page(request):
    """Показать категории, количество и сумму расходов по каждой из них."""
    with closing(_open_row_connection()) as connection:
        categories = connection.execute(
            SQL_QUERIES[10]
        ).fetchall()
        empty_categories = connection.execute(
            SQL_QUERIES[15]
        ).fetchall()

    return render(
        request,
        "catalogs/category_list.html",
        {
            "categories": categories,
            "empty_categories": empty_categories,
        },
    )


def departments_page(request):
    """Показать подразделения и суммы расходов каждого подразделения."""
    with closing(_open_row_connection()) as connection:
        departments = connection.execute(
            SQL_QUERIES[11]
        ).fetchall()

    return render(
        request,
        "catalogs/department_list.html",
        {"departments": departments},
    )


def documents_page(request):
    """Показать документы и расходы, связанные с каждым документом."""
    with closing(_open_row_connection()) as connection:
        documents = connection.execute(
            SQL_QUERIES[12]
        ).fetchall()

    return render(
        request,
        "catalogs/document_list.html",
        {"documents": documents},
    )
