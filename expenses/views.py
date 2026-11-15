"""Представления расходов и статистики на основе Django ORM."""

from datetime import date
from decimal import Decimal, InvalidOperation

from django.core.paginator import Paginator
from django.db.models import (
    Avg,
    Count,
    DecimalField,
    F,
    Max,
    Min,
    Q,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from catalogs.models import Category, Department
from .models import Expense


MONEY_OUTPUT_FIELD = DecimalField(max_digits=14, decimal_places=2)
ZERO_AMOUNT = Value(Decimal("0.00"), output_field=MONEY_OUTPUT_FIELD)

SORT_OPTIONS = {
    "amount_desc": ("-amount", "pk"),
    "amount_asc": ("amount", "pk"),
    "category": ("category__name", "pk"),
    "department": ("department__name", "pk"),
    "date_desc": ("-expense_date", "-pk"),
    "date_asc": ("expense_date", "pk"),
}
PAGE_SIZE = 10


def _parse_positive_int(value: str) -> int | None:
    """Преобразовать параметр запроса в положительное целое число."""
    try:
        result = int(value)
    except (TypeError, ValueError):
        return None

    return result if result > 0 else None


def _parse_amount(value: str) -> tuple[Decimal | None, str]:
    """Проверить неотрицательную сумму из параметра запроса."""
    if not value:
        return None, ""

    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return None, "Введите корректную сумму."

    if not amount.is_finite():
        return None, "Введите корректную сумму."

    if amount < 0:
        return None, "Сумма не может быть отрицательной."

    return amount, ""


def _parse_date(value: str) -> tuple[date | None, str]:
    """Проверить дату в формате YYYY-MM-DD из строки запроса."""
    if not value:
        return None, ""

    parsed = parse_date(value)
    if parsed is None:
        return None, "Введите дату в формате ГГГГ-ММ-ДД."
    return parsed, ""


def _combine_errors(*errors: str) -> str:
    """Объединить сообщения валидации, не дублируя пустые значения."""
    return " ".join(error for error in errors if error)


def expense_list(request: HttpRequest) -> HttpResponse:
    """Показать расходы с ORM-фильтрацией, сортировкой и пагинацией."""
    raw_min_amount = request.GET.get("min_amount", "").strip()
    min_amount, amount_error = _parse_amount(raw_min_amount)

    raw_date_from = request.GET.get("date_from", "").strip()
    raw_date_to = request.GET.get("date_to", "").strip()
    date_from, date_from_error = _parse_date(raw_date_from)
    date_to, date_to_error = _parse_date(raw_date_to)
    if date_from and date_to and date_from > date_to:
        date_range_error = "Начальная дата не может быть позже конечной."
    else:
        date_range_error = ""

    category_id = _parse_positive_int(
        request.GET.get("category_id", "")
    )
    department_id = _parse_positive_int(
        request.GET.get("department_id", "")
    )
    search_text = request.GET.get("q", "").strip()
    document_query = request.GET.get("document", "").strip()

    requested_status = request.GET.get("status", "").strip()
    valid_statuses = {value for value, _label in Expense.Status.choices}
    selected_status = (
        requested_status if requested_status in valid_statuses else ""
    )

    sort_key = request.GET.get("sort", "amount_desc")
    if sort_key not in SORT_OPTIONS:
        sort_key = "amount_desc"

    # Загружаем связанные справочники вместе с расходами.
    expenses = Expense.objects.select_related(
        "category",
        "department",
        "document",
    )

    if min_amount is not None:
        expenses = expenses.above_amount(min_amount)

    if category_id is not None:
        expenses = expenses.filter(category_id=category_id)

    if department_id is not None:
        expenses = expenses.filter(department_id=department_id)

    if selected_status:
        expenses = expenses.filter(status=selected_status)

    if date_from_error or date_to_error or date_range_error:
        expenses = expenses.none()
    else:
        if date_from:
            expenses = expenses.filter(expense_date__gte=date_from)
        if date_to:
            expenses = expenses.filter(expense_date__lte=date_to)

    if search_text:
        expenses = expenses.filter(
            Q(category__name__icontains=search_text)
            | Q(department__name__icontains=search_text)
            | Q(document__number__icontains=search_text)
        )

    if document_query:
        expenses = expenses.filter(
            document__number__icontains=document_query
        )

    # Сортируем только по заранее разрешённым полям.
    expenses = expenses.order_by(*SORT_OPTIONS[sort_key])

    paginator = Paginator(expenses, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "expenses": page_obj,
        "page_obj": page_obj,
        "expense_count": paginator.count,
        "categories": Category.objects.order_by("name"),
        "departments": Department.objects.order_by("name"),
        "status_choices": Expense.Status.choices,
        "filters": {
            "min_amount": raw_min_amount,
            "category_id": category_id,
            "department_id": department_id,
            "q": search_text,
            "document": document_query,
            "status": selected_status,
            "date_from": raw_date_from,
            "date_to": raw_date_to,
            "sort": sort_key,
        },
        "error": _combine_errors(
            amount_error,
            date_from_error,
            date_to_error,
            date_range_error,
        ),
    }

    return render(request, "expenses/expense_list.html", context)


def expense_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """Открыть подробную карточку расхода по уникальному slug."""
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


def expense_detail_legacy(
    request: HttpRequest,
    expense_id: int,
) -> HttpResponse:
    """Перенаправить старый числовой адрес на канонический адрес по slug."""
    expense = get_object_or_404(Expense, pk=expense_id)
    return redirect(expense.get_absolute_url(), permanent=True)


def expense_statistics(request: HttpRequest) -> HttpResponse:
    """Показать сводные показатели и группировки через Django ORM."""
    raw_threshold = request.GET.get("threshold", "10000").strip()
    threshold, error = _parse_amount(raw_threshold)

    if threshold is None:
        threshold = Decimal("10000.00")
        if not error:
            error = "Порог должен быть неотрицательным числом."

    # Отменённые записи остаются в журнале, но не суммируются как расходы.
    summary = Expense.objects.aggregate(
        expense_count=Count(
            "pk",
            filter=~Q(status=Expense.Status.CANCELLED),
        ),
        cancelled_count=Count(
            "pk",
            filter=Q(status=Expense.Status.CANCELLED),
        ),
        pending_count=Count(
            "pk",
            filter=Q(status=Expense.Status.PENDING),
        ),
        approved_count=Count(
            "pk",
            filter=Q(status=Expense.Status.APPROVED),
        ),
        paid_count=Count(
            "pk",
            filter=Q(status=Expense.Status.PAID),
        ),
        total_amount=Coalesce(
            Sum(
                "amount",
                filter=~Q(status=Expense.Status.CANCELLED),
            ),
            ZERO_AMOUNT,
            output_field=MONEY_OUTPUT_FIELD,
        ),
        average_amount=Coalesce(
            Avg(
                "amount",
                filter=~Q(status=Expense.Status.CANCELLED),
            ),
            ZERO_AMOUNT,
            output_field=MONEY_OUTPUT_FIELD,
        ),
        min_amount=Coalesce(
            Min(
                "amount",
                filter=~Q(status=Expense.Status.CANCELLED),
            ),
            ZERO_AMOUNT,
            output_field=MONEY_OUTPUT_FIELD,
        ),
        max_amount=Coalesce(
            Max(
                "amount",
                filter=~Q(status=Expense.Status.CANCELLED),
            ),
            ZERO_AMOUNT,
            output_field=MONEY_OUTPUT_FIELD,
        ),
    )

    active_filter = ~Q(expenses__status=Expense.Status.CANCELLED)
    category_groups = Category.objects.annotate(
        category_name=F("name"),
        expense_count=Count("expenses", filter=active_filter),
        total_amount=Coalesce(
            Sum("expenses__amount", filter=active_filter),
            ZERO_AMOUNT,
            output_field=MONEY_OUTPUT_FIELD,
        ),
    )
    category_statistics = category_groups.order_by(
        "-total_amount", "name"
    ).values("category_name", "expense_count", "total_amount")
    high_spend_categories = category_groups.filter(
        total_amount__gt=threshold
    ).order_by("-total_amount", "name").values(
        "category_name", "expense_count", "total_amount"
    )

    department_groups = Department.objects.annotate(
        department_name=F("name"),
        expense_count=Count("expenses", filter=active_filter),
        total_amount=Coalesce(
            Sum("expenses__amount", filter=active_filter),
            ZERO_AMOUNT,
            output_field=MONEY_OUTPUT_FIELD,
        ),
    )
    department_statistics = department_groups.order_by(
        "-total_amount", "name"
    ).values("department_name", "expense_count", "total_amount")
    high_spend_departments = department_groups.filter(
        total_amount__gte=threshold
    ).order_by("-total_amount", "name").values(
        "department_name", "expense_count", "total_amount"
    )

    context = {
        "summary": summary,
        "category_statistics": category_statistics,
        "department_statistics": department_statistics,
        "high_spend_categories": high_spend_categories,
        "high_spend_departments": high_spend_departments,
        "threshold": raw_threshold,
        "error": error,
    }
    return render(request, "expenses/expense_statistics.html", context)
