
"""Представления для просмотра, поиска и анализа расходов."""

from decimal import Decimal, InvalidOperation

from django.core.paginator import Paginator
from django.db.models import (
    Avg,
    Count,
    Max,
    Min,
    Q,
    Sum,
)
from django.shortcuts import get_object_or_404, redirect, render


from catalogs.models import Category, Department
from .models import Expense


PAGE_SIZE = 10

SORT_OPTIONS = {
    "amount_desc": "-amount",
    "amount_asc": "amount",
    "category": "category__name",
    "department": "department__name",
}


def _parse_amount(value):
    """Проверить сумму, введённую пользователем."""
    if not value:
        return None, ""

    try:
        amount = Decimal(value)
    except InvalidOperation:
        return None, "Введите корректную сумму."

    if amount < 0:
        return None, "Сумма не может быть отрицательной."

    return amount, ""


def _ensure_expense_slug(expense):
    """Создать slug для старых записей, если он отсутствует."""
    if not expense.slug:
        expense.slug = f"expense-{expense.pk}"
        expense.save(update_fields=["slug"])


def expense_list(request):
    """Показать список расходов с фильтрацией и сортировкой."""

    min_amount, error = _parse_amount(
        request.GET.get("min_amount", "").strip()
    )

    category_id = request.GET.get("category_id", "").strip()
    department_id = request.GET.get("department_id", "").strip()
    search_text = request.GET.get("q", "").strip()

    sort_key = request.GET.get("sort", "amount_desc")
    sort_field = SORT_OPTIONS.get(
        sort_key,
        SORT_OPTIONS["amount_desc"],
    )

    expenses = Expense.objects.select_related(
        "category",
        "department",
        "document",
    )

    if min_amount is not None:
        expenses = expenses.filter(amount__gte=min_amount)

    if category_id.isdigit():
        expenses = expenses.filter(category_id=int(category_id))

    if department_id.isdigit():
        expenses = expenses.filter(department_id=int(department_id))

    if search_text:
        expenses = expenses.filter(
            Q(category__name__icontains=search_text)
            | Q(department__name__icontains=search_text)
            | Q(document__number__icontains=search_text)
            | Q(comment__icontains=search_text)
        )

    expenses = expenses.order_by(sort_field, "pk")

    paginator = Paginator(expenses, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Заполняем slug у старых записей, если он ещё отсутствует.
    for expense in page_obj.object_list:
        _ensure_expense_slug(expense)

    context = {
        "expenses": page_obj,
        "page_obj": page_obj,
        "categories": Category.objects.all().order_by("name"),
        "departments": Department.objects.all().order_by("name"),
        "filters": {
            "min_amount": request.GET.get("min_amount", ""),
            "category_id": category_id,
            "department_id": department_id,
            "q": search_text,
            "sort": sort_key if sort_key in SORT_OPTIONS else "amount_desc",
        },
        "error": error,
    }

    return render(
        request,
        "expenses/expense_list.html",
        context,
    )


def expense_detail(request, slug):
    """Показать подробную информацию о расходе."""

    expense = get_object_or_404(
        Expense.objects.select_related(
            "category",
            "department",
            "document",
        ),
        slug=slug,
    )

    return render(
        request,
        "expenses/expense_detail.html",
        {"expense": expense},
    )


def expense_detail_legacy(request, expense_id):
    """Перенаправить старый числовой адрес на страницу со slug."""

    expense = get_object_or_404(Expense, pk=expense_id)

    _ensure_expense_slug(expense)

    return redirect(
        "expenses:expense_detail",
        slug=expense.slug,
        permanent=True,
    )


def expense_statistics(request):
    """Показать общую статистику расходов организации."""

    raw_threshold = request.GET.get("threshold", "10000").strip()
    threshold, error = _parse_amount(raw_threshold)

    if threshold is None:
        threshold = Decimal("10000")
        if not error:
            error = "Порог должен быть неотрицательным числом."

    summary = Expense.objects.aggregate(
        total_count=Count("id"),
        total_amount=Sum("amount"),
        average_amount=Avg("amount"),
        min_amount=Min("amount"),
        max_amount=Max("amount"),
    )

    category_statistics = (
        Category.objects.annotate(
            expenses_count=Count("expenses"),
            total_amount=Sum("expenses__amount"),
        )
        .order_by("-total_amount", "name")
    )

    department_statistics = (
        Department.objects.annotate(
            expenses_count=Count("expenses"),
            total_amount=Sum("expenses__amount"),
        )
        .order_by("-total_amount", "name")
    )

    high_spend_categories = (
        Category.objects.annotate(
            total_amount=Sum("expenses__amount"),
        )
        .filter(total_amount__gt=threshold)
        .order_by("-total_amount")
    )

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
