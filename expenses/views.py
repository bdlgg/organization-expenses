"""Представления для просмотра, поиска и анализа расходов организации."""

import re
import sqlite3
from contextlib import closing
from pathlib import Path

from django.shortcuts import render

from db.database import get_connection


# Путь к файлу с SQL-запросами.
SQL_FILE = Path(__file__).resolve().parents[1] / "sql" / "queries.sql"


def _load_sql_queries() -> dict[int, str]:
    """Загрузить SQL-запросы из файла и сопоставить их с номерами."""
    content = SQL_FILE.read_text(encoding="utf-8")

    # Разделяем файл по комментариям с номерами запросов: -- 1., -- 2. и т. д.
    parts = re.split(r"(?m)^--\s*(\d+)\.\s*.*$", content)

    queries = {}

    for index in range(1, len(parts), 2):
        query_number = int(parts[index])
        query_content = parts[index + 1].strip()

        # Убираем завершающую точку с запятой.
        query_content = query_content.rstrip(";").strip()

        if query_content:
            queries[query_number] = query_content

    return queries


# Загружаем SQL-запросы один раз при загрузке представлений.
SQL_QUERIES = _load_sql_queries()


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

        # Эти два запроса нужны для списков фильтров.
        # В текущем queries.sql отдельных запросов для них нет.
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

    # Запрос №13 использует порог 10000.
    # Заменяем его на параметр ?, чтобы можно было задавать порог со страницы.
    high_spend_query = re.sub(
        r"HAVING\s+SUM\s*\(\s*e\.amount\s*\)\s*>\s*10000",
        "HAVING SUM(e.amount) > ?",
        SQL_QUERIES[13],
        count=1,
        flags=re.IGNORECASE,
    )

    with closing(_open_row_connection()) as connection:

        # Запрос №8: количество, общая и средняя сумма расходов.
        summary = connection.execute(
            SQL_QUERIES[8]
        ).fetchone()

        # Запрос №9: минимальная и максимальная сумма расхода.
        extremes = connection.execute(
            SQL_QUERIES[9]
        ).fetchone()

        # Объединяем результаты двух запросов в один словарь.
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
            high_spend_query,
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

    return render(
        request,
        "expenses/expense_statistics.html",
        context,
    )