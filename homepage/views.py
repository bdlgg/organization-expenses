"""Представления главной страницы и страницы 404."""

import sqlite3
from contextlib import closing

from django.shortcuts import render

from db.database import get_connection
from db.queries import SQL_QUERIES


def _open_row_connection() -> sqlite3.Connection:
    """Открыть SQLite-соединение с доступом к полям строк по именам."""
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    return connection


def index(request):
    """Показать краткую сводку расходов из SQLite."""
    with closing(_open_row_connection()) as connection:
        summary = connection.execute(
            SQL_QUERIES[8]
        ).fetchone()

    return render(request, "homepage/index.html", {"summary": summary})


def page_not_found(request, exception):
    """Вернуть оформленную страницу 404 для неизвестного URL."""
    return render(request, "homepage/404.html", status=404)
