"""Представления для просмотра, поиска и анализа расходов организации."""

import re
import sqlite3
from contextlib import closing

from django.shortcuts import render

from db.database import get_connection
from db.queries import SQL_QUERIES


def _open_row_connection() -> sqlite3.Connection:
    """Открыть соединение, строки которого доступны по именам столбцов."""
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    return connection


def _parse_positive_int(value: str) -> int | None:
    """Преобразовать параметр URL в положительное целое число."""
    try:
        result = int(value)
    except (TypeError, ValueError):
        return None

    return result if result > 0 else None


def _parse_amount(value: str) -> tuple[float | None, str]:
    """Проверить минимальную сумму из формы поиска."""
    if not value:
        return None, ""

    try:
        amount = float(value)
    except ValueError:
        return None, "Введите корректную сумму."

    if amount < 0:
        return None, "Сумма не может быть отрицательной."

    return amount, ""


def _split_order_by(query: str) -> tuple[str, str]:
    """Разделить запрос на основную часть и сортировку."""
    match = re.search(r"\bORDER\s+BY\b", query, flags=re.IGNORECASE)

    if match is None:
        return query.strip(), ""

    return (
        query[:match.start()].strip(),
        query[match.start():].strip(),
    )


SORT_OPTIONS = {
    "amount_desc": "e.amount DESC, e.id",
    "amount_asc": "e.amount ASC, e.id",
    "category": "c.name, e.id",
    "department": "d.name, e.id",
}


def expense_list(request):
    """Показать расходы с фильтрацией и сортировкой средствами SQL."""
    min_amount, error = _parse_amount(
        request.GET.get("min_amount", "").strip()
    )

    category_id = _parse_positive_int(
        request.GET.get("category_id", "")
    )

    department_id = _parse_positive_int(
        request.GET.get("department_id", "")
    )

    search_text = request.GET.get("q", "").strip()

    sort_key = request.GET.get("sort", "amount_desc")
    sort_sql = SORT_OPTIONS.get(
        sort_key,
        SORT_OPTIONS["amount_desc"],
    )

    conditions = []
    parameters = []

    if min_amount is not None:
        conditions.append("e.amount >= ?")
        parameters.append(min_amount)

    if category_id is not None:
        conditions.append("e.category_id = ?")
        parameters.append(category_id)

    if department_id is not None:
        conditions.append("e.department_id = ?")
        parameters.append(department_id)

    if search_text:
        conditions.append(
            "(c.name LIKE ? OR d.name LIKE ? OR doc.number LIKE ?)"
        )

        search_pattern = f"%{search_text}%"
        parameters.extend(
            [search_pattern, search_pattern, search_pattern]
        )

    # Используем запрос №1 из queries.sql.
    query, _ = _split_order_by(SQL_QUERIES[1])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY " + sort_sql

    with closing(_open_row_connection()) as connection:
        expenses = connection.execute(
            query,
            parameters,
        ).fetchall()

        # Запросы №16 и №17: данные для списков фильтров.
        categories = connection.execute(
            SQL_QUERIES[16]
        ).fetchall()

        departments = connection.execute(
            SQL_QUERIES[17]
        ).fetchall()

    context = {
        "expenses": expenses,
        "categories": categories,
        "departments": departments,
        "filters": {
            "min_amount": request.GET.get("min_amount", ""),
            "category_id": category_id,
            "department_id": department_id,
            "q": search_text,
            "sort": (
                sort_key
                if sort_key in SORT_OPTIONS
                else "amount_desc"
            ),
        },
        "error": error,
    }

    return render(
        request,
        "expenses/expense_list.html",
        context,
    )


def expense_detail(request, expense_id: int):
    """Получить один расход и связанные с ним справочные данные."""

    # Используем запрос №1 из queries.sql без исходной сортировки.
    query, _ = _split_order_by(SQL_QUERIES[1])
    query += " WHERE e.id = ?"

    with closing(_open_row_connection()) as connection:
        expense = connection.execute(
            query,
            (expense_id,),
        ).fetchone()

    if expense is None:
        return render(
            request,
            "expenses/expense_detail.html",
            {"expense": None},
            status=404,
        )

    return render(
        request,
        "expenses/expense_detail.html",
        {"expense": expense},
    )


def expense_statistics(request):
    """Показать общие показатели и группировку расходов по справочникам."""
    raw_threshold = request.GET.get("threshold", "10000").strip()

    threshold, error = _parse_amount(raw_threshold)

    if threshold is None:
        threshold = 10000.0

        if not error:
            error = "Порог должен быть неотрицательным числом."

    with closing(_open_row_connection()) as connection:

        # Запрос №8: общая статистика расходов.
        summary = connection.execute(
            SQL_QUERIES[8]
        ).fetchone()

        # Запрос №9: минимальная и максимальная сумма расхода.
        extremes = connection.execute(
            SQL_QUERIES[9]
        ).fetchone()

        # Объединяем результаты двух запросов.
        summary = {
            **dict(summary),
            **dict(extremes),
        }

        # Запрос №10: статистика по категориям.
        category_statistics = connection.execute(
            SQL_QUERIES[10]
        ).fetchall()

        # Запрос №11: статистика по подразделениям.
        department_statistics = connection.execute(
            SQL_QUERIES[11]
        ).fetchall()

        # Запрос №13: категории, превысившие заданный порог.
        high_spend_categories = connection.execute(
            SQL_QUERIES[13],
            (threshold,),
        ).fetchall()

        # Запрос №14: подразделения с расходами не менее заданного порога.
        high_spend_departments = connection.execute(
            SQL_QUERIES[14],
            (threshold,),
        ).fetchall()

    context = {
        "summary": summary,
        "category_statistics": category_statistics,
        "department_statistics": department_statistics,
        "high_spend_categories": high_spend_categories,
        "high_spend_departments": high_spend_departments,
        "threshold": raw_threshold,
        "error": error,
    }

    return render(
        request,
        "expenses/expense_statistics.html",
        context,
    )
