"""Представления справочников, данные которых хранятся в SQLite."""

import sqlite3
from contextlib import closing

from django.shortcuts import render

from db.database import get_connection


def _open_row_connection() -> sqlite3.Connection:
    """Открыть соединение SQLite с доступом к полям по именам."""
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    return connection


def categories_page(request):
    """Показать категории, количество и сумму расходов по каждой из них."""
    query = """
        SELECT
            c.id,
            c.name,
            COUNT(e.id) AS expense_count,
            COALESCE(SUM(e.amount), 0) AS total_amount
        FROM categories AS c
        LEFT JOIN expenses AS e ON e.category_id = c.id
        GROUP BY c.id, c.name
        ORDER BY c.name
    """
    with closing(_open_row_connection()) as connection:
        categories = connection.execute(query).fetchall()
    return render(
        request,
        "catalogs/category_list.html",
        {"categories": categories},
    )


def departments_page(request):
    """Показать подразделения и суммы расходов каждого подразделения."""
    query = """
        SELECT
            d.id,
            d.name,
            COUNT(e.id) AS expense_count,
            COALESCE(SUM(e.amount), 0) AS total_amount
        FROM departments AS d
        LEFT JOIN expenses AS e ON e.department_id = d.id
        GROUP BY d.id, d.name
        ORDER BY d.name
    """
    with closing(_open_row_connection()) as connection:
        departments = connection.execute(query).fetchall()
    return render(
        request,
        "catalogs/department_list.html",
        {"departments": departments},
    )


def documents_page(request):
    """Показать документы и расходы, связанные с каждым документом."""
    query = """
        SELECT
            doc.id,
            doc.number,
            COUNT(e.id) AS expense_count,
            COALESCE(SUM(e.amount), 0) AS total_amount
        FROM documents AS doc
        LEFT JOIN expenses AS e ON e.document_id = doc.id
        GROUP BY doc.id, doc.number
        ORDER BY doc.number
    """
    with closing(_open_row_connection()) as connection:
        documents = connection.execute(query).fetchall()
    return render(
        request,
        "catalogs/document_list.html",
        {"documents": documents},
    )
