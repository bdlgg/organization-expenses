"""Представления расходов и статистики на основе Django ORM."""

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
from django.shortcuts import get_object_or_404, render

from catalogs.models import Category, Department
from .models import Expense


MONEY_OUTPUT_FIELD = DecimalField(max_digits=14, decimal_places=2)
ZERO_AMOUNT = Value(Decimal("0.00"), output_field=MONEY_OUTPUT_FIELD)

SORT_OPTIONS = {
    "amount_desc": ("-amount", "pk"),
    "amount_asc": ("amount", "pk"),
    "category": ("category__name", "pk"),
    "department": ("department__name", "pk"),
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


def expense_list(request):
    """Показать расходы с ORM-фильтрацией, сортировкой и пагинацией."""
    raw_min_amount = request.GET.get("min_amount", "").strip()
    min_amount, error = _parse_amount(raw_min_amount)

    category_id = _parse_positive_int(
        request.GET.get("category_id", "")
    )
    department_id = _parse_positive_int(
        request.GET.get("department_id", "")
    )
    search_text = request.GET.get("q", "").strip()
    document_query = request.GET.get("document", "").strip()

    sort_key = request.GET.get("sort", "amount_desc")
    if sort_key not in SORT_OPTIONS:
        sort_key = "amount_desc"

    # Получаем связанные справочники одним запросом вместе с расходами.
    expenses = Expense.objects.select_related(
        "category",
        "department",
        "document",
    )

    # Фильтрация по сумме и внешним ключам.
    if min_amount is not None:
        expenses = expenses.filter(amount__gte=min_amount)

    if category_id is not None:
        expenses = expenses.filter(category_id=category_id)

    if department_id is not None:
        expenses = expenses.filter(department_id=department_id)

    # Поиск по нескольким строковым полям связанных моделей.
    if search_text:
        expenses = expenses.filter(
            Q(category__name__icontains=search_text)
            | Q(department__name__icontains=search_text)
            | Q(document__number__icontains=search_text)
        )

    # Отдельный поиск по номеру документа.
    if document_query:
        expenses = expenses.filter(
            document__number__icontains=document_query
        )

    # Поле сортировки выбирается только из разрешённого списка.
    expenses = expenses.order_by(*SORT_OPTIONS[sort_key])

    # Пагинация применяется после фильтрации и сортировки.
    paginator = Paginator(expenses, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "expenses": page_obj,
        "page_obj": page_obj,
        "expense_count": paginator.count,
        "categories": Category.objects.order_by("name"),
        "departments": Department.objects.order_by("name"),
        "filters": {
            "min_amount": raw_min_amount,
            "category_id": category_id,
            "department_id": department_id,
            "q": search_text,
            "document": document_query,
            "sort": sort_key,
        },
        "error": error,
    }

    return render(request, "expenses/expense_list.html", context)


def expense_detail(request, expense_id: int):
    """Получить один расход вместе со связанными справочниками."""
    expense = get_object_or_404(
        Expense.objects.select_related(
            "category",
            "department",
            "document",
        ),
        pk=expense_id,
    )

    return render(
        request,
        "expenses/expense_detail.html",
        {"expense": expense},
    )


def expense_statistics(request):
    """Показать сводные показатели и группировки через Django ORM."""
    raw_threshold = request.GET.get("threshold", "10000").strip()
    threshold, error = _parse_amount(raw_threshold)

    if threshold is None:
        threshold = Decimal("10000.00")
        if not error:
            error = "Порог должен быть неотрицательным числом."

    # aggregate() возвращает одну общую сводку по всем расходам.
    summary = Expense.objects.aggregate(
        expense_count=Count("pk"),
        total_amount=Coalesce(
            Sum("amount"), ZERO_AMOUNT,
            output_field=MONEY_OUTPUT_FIELD,
        ),
        average_amount=Coalesce(
            Avg("amount"), ZERO_AMOUNT,
            output_field=MONEY_OUTPUT_FIELD,
        ),
        min_amount=Coalesce(
            Min("amount"), ZERO_AMOUNT,
            output_field=MONEY_OUTPUT_FIELD,
        ),
        max_amount=Coalesce(
            Max("amount"), ZERO_AMOUNT,
            output_field=MONEY_OUTPUT_FIELD,
        ),
    )

    # Считаем расходы по категориям, включая категории с нулевой суммой.
    category_groups = Category.objects.annotate(
        category_name=F("name"),
        expense_count=Count("expenses"),
        total_amount=Coalesce(
            Sum("expenses__amount"), ZERO_AMOUNT,
            output_field=MONEY_OUTPUT_FIELD,
        ),
    )
    category_statistics = category_groups.order_by(
        "-total_amount", "name"
    ).values(
        "category_name",
        "expense_count",
        "total_amount",
    )

    # Фильтрация агрегированных групп формирует SQL HAVING через ORM.
    high_spend_categories = category_groups.filter(
        total_amount__gt=threshold
    ).order_by("-total_amount", "name").values(
        "category_name",
        "expense_count",
        "total_amount",
    )

    # Те же показатели по подразделениям.
    department_groups = Department.objects.annotate(
        department_name=F("name"),
        expense_count=Count("expenses"),
        total_amount=Coalesce(
            Sum("expenses__amount"), ZERO_AMOUNT,
            output_field=MONEY_OUTPUT_FIELD,
        ),
    )
    department_statistics = department_groups.order_by(
        "-total_amount", "name"
    ).values(
        "department_name",
        "expense_count",
        "total_amount",
    )
    high_spend_departments = department_groups.filter(
        total_amount__gte=threshold
    ).order_by("-total_amount", "name").values(
        "department_name",
        "expense_count",
        "total_amount",
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
