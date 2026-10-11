from pathlib import Path
from typing import List

from django.http import HttpResponse
from django.utils.html import escape

from homepage.views import page
from models.expenses import Expense, find_expense_by_id
from storage import (
    load_categories,
    load_departments,
    load_documents,
    load_expenses as load_expenses_from_json,
)

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_expenses() -> List[Expense]:
    """Загрузить справочники и расходы из JSON."""
    categories = load_categories(
        str(BASE_DIR / "data" / "categories.json")
    )
    departments = load_departments(
        str(BASE_DIR / "data" / "departments.json")
    )
    documents = load_documents(
        str(BASE_DIR / "data" / "documents.json")
    )

    return load_expenses_from_json(
        str(BASE_DIR / "data" / "expenses.json"),
        categories,
        departments,
        documents,
    )


def expense_list(request):
    """Показать список расходов из JSON."""
    expenses = _load_expenses()
    items = ""

    for expense in expenses:
        category = escape(expense.category.name)
        department = escape(expense.department.name)
        document = escape(expense.document.number)

        items += f"""
        <a class="list-group-item list-group-item-action"
           href="/expenses/{expense.id}/">
            <div class="d-flex flex-wrap justify-content-between gap-2">
                <strong>Расход №{expense.id}</strong>
                <span class="fw-semibold">{expense.amount:.2f} руб.</span>
            </div>
            <div class="text-secondary small mt-1">
                Категория: {category} · Подразделение: {department}
                · Документ: {document}
            </div>
        </a>
        """

    if not items:
        items = (
            '<div class="list-group-item">'
            "В файле пока нет расходов."
            "</div>"
        )

    content = f"""
    <h1 class="mb-3">Расходы организации</h1>
    <p class="text-secondary">
        Данные загружаются из <code>data/expenses.json</code> и связанных
        JSON-справочников.
    </p>
    <div class="list-group">{items}</div>
    """

    return HttpResponse(page("Расходы", content))


def expense_detail(request, expense_id: int):
    """Показать подробную информацию о расходе по ID."""
    expenses = _load_expenses()
    expense = find_expense_by_id(expenses, expense_id)

    if expense is None:
        content = f"""
        <section class="page-panel p-4">
            <h1 class="text-danger">Расход не найден</h1>
            <p>Расход с ID {expense_id} отсутствует в данных.</p>
            <a class="btn btn-outline-secondary" href="/expenses/">
                Вернуться к списку расходов
            </a>
        </section>
        """
        return HttpResponse(
            page("Расход не найден", content),
            status=404,
        )

    category = escape(expense.category.name)
    department = escape(expense.department.name)
    document = escape(expense.document.number)

    content = f"""
    <section class="page-panel p-4">
        <h1 class="h3">Расход №{expense.id}</h1>
        <dl class="row mt-4 mb-4">
            <dt class="col-sm-4">Сумма</dt>
            <dd class="col-sm-8">{expense.amount:.2f} руб.</dd>
            <dt class="col-sm-4">Категория</dt>
            <dd class="col-sm-8">{category}</dd>
            <dt class="col-sm-4">Подразделение</dt>
            <dd class="col-sm-8">{department}</dd>
            <dt class="col-sm-4">Документ</dt>
            <dd class="col-sm-8">{document}</dd>
        </dl>
        <a class="btn btn-outline-secondary" href="/expenses/">
            Вернуться к списку расходов
        </a>
    </section>
    """

    return HttpResponse(page(f"Расход №{expense.id}", content))
