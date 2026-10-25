"""Представления для просмотра, поиска и анализа расходов организации."""

import sqlite3
from contextlib import closing

from django.shortcuts import render

from db.database import get_connection

BASE_EXPENSE_QUERY = """
    SELECT
        e.id,
        e.amount,
        c.name AS category_name,
        d.name AS department_name,
        doc.number AS document_number
    FROM expenses AS e
    JOIN categories AS c ON c.id = e.category_id
    JOIN departments AS d ON d.id = e.department_id
    JOIN documents AS doc ON doc.id = e.document_id
"""

SORT_OPTIONS = {
    "amount_desc": "e.amount DESC, e.id",
    "amount_asc": "e.amount ASC, e.id",
    "category": "c.name, e.id",
    "department": "d.name, e.id",
}


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
    sort_sql = SORT_OPTIONS.get(sort_key, SORT_OPTIONS["amount_desc"])

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
        parameters.extend([search_pattern, search_pattern, search_pattern])

    query = BASE_EXPENSE_QUERY
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY " + sort_sql

    with closing(_open_row_connection()) as connection:
        expenses = connection.execute(query, parameters).fetchall()
        categories = connection.execute(
            "SELECT id, name FROM categories ORDER BY name"
        ).fetchall()
        departments = connection.execute(
            "SELECT id, name FROM departments ORDER BY name"
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
            "sort": sort_key if sort_key in SORT_OPTIONS else "amount_desc",
        },
        "error": error,
    }
    return render(request, "expenses/expense_list.html", context)


def expense_detail(request, expense_id: int):
    """Получить один расход и связанные с ним справочные данные."""
    with closing(_open_row_connection()) as connection:
        expense = connection.execute(
            BASE_EXPENSE_QUERY + " WHERE e.id = ?",
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
        summary = connection.execute(
            """
            SELECT
                COUNT(*) AS expense_count,
                COALESCE(SUM(amount), 0) AS total_amount,
                COALESCE(AVG(amount), 0) AS average_amount,
                COALESCE(MIN(amount), 0) AS min_amount,
                COALESCE(MAX(amount), 0) AS max_amount
            FROM expenses
            """
        ).fetchone()
        category_statistics = connection.execute(
            """
            SELECT
                c.id,
                c.name AS category_name,
                COUNT(e.id) AS expense_count,
                COALESCE(SUM(e.amount), 0) AS total_amount
            FROM categories AS c
            LEFT JOIN expenses AS e ON e.category_id = c.id
            GROUP BY c.id, c.name
            ORDER BY total_amount DESC, c.name
            """
        ).fetchall()
        department_statistics = connection.execute(
            """
            SELECT
                d.id,
                d.name AS department_name,
                COUNT(e.id) AS expense_count,
                COALESCE(SUM(e.amount), 0) AS total_amount
            FROM departments AS d
            LEFT JOIN expenses AS e ON e.department_id = d.id
            GROUP BY d.id, d.name
            ORDER BY total_amount DESC, d.name
            """
        ).fetchall()
        high_spend_categories = connection.execute(
            """
            SELECT
                c.name AS category_name,
                COUNT(e.id) AS expense_count,
                SUM(e.amount) AS total_amount
            FROM categories AS c
            JOIN expenses AS e ON e.category_id = c.id
            GROUP BY c.id, c.name
            HAVING SUM(e.amount) >= ?
            ORDER BY total_amount DESC
            """,
            (threshold,),
        ).fetchall()

    context = {
        "summary": summary,
        "category_statistics": category_statistics,
        "department_statistics": department_statistics,
        "high_spend_categories": high_spend_categories,
        "threshold": raw_threshold,
        "error": error,
    }
    return render(request, "expenses/expense_statistics.html", context)
