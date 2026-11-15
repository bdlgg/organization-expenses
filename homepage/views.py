"""Представления главной страницы и страницы 404."""

import sqlite3
from contextlib import closing

from django.shortcuts import render

from db.database import get_connection


def _open_row_connection() -> sqlite3.Connection:
    """Открыть SQLite-соединение с доступом к полям строк по именам."""
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    return connection


def index(request):
    """Показать краткую сводку расходов из SQLite."""
    with closing(_open_row_connection()) as connection:
        summary = connection.execute(
            """
            SELECT
                COUNT(*) AS expense_count,
                COALESCE(SUM(amount), 0) AS total_amount,
                COALESCE(AVG(amount), 0) AS average_amount
            FROM expenses
            """
        ).fetchone()

    return render(request, "homepage/index.html", {"summary": summary})


def page_not_found(request, exception):
    """Вернуть оформленную страницу 404 для неизвестного URL."""
    return render(request, "homepage/404.html", status=404)
