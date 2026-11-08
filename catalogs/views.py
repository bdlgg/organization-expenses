"""Представления справочников на основе Django ORM."""

from decimal import Decimal

from django.db.models import Count, DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import render

from expenses.models import Expense
from .models import Category, Department, Document


MONEY_OUTPUT_FIELD = DecimalField(max_digits=14, decimal_places=2)
ZERO_AMOUNT = Value(Decimal("0.00"), output_field=MONEY_OUTPUT_FIELD)


def categories_page(request):
    """Показать категории, количество и сумму расходов по каждой из них."""
    categories = Category.objects.annotate(
        category_name=F("name"),
        expense_count=Count("expenses"),
        total_amount=Coalesce(
            Sum("expenses__amount"), ZERO_AMOUNT,
            output_field=MONEY_OUTPUT_FIELD,
        ),
    ).order_by("-total_amount", "name").values(
        "category_name",
        "expense_count",
        "total_amount",
    )

    # Исключаем категории, встречающиеся во внешних ключах расходов.
    empty_categories = Category.objects.exclude(
        pk__in=Expense.objects.values("category_id")
    ).order_by("name")

    return render(
        request,
        "catalogs/category_list.html",
        {
            "categories": categories,
            "empty_categories": empty_categories,
        },
    )


def departments_page(request):
    """Показать подразделения и суммы расходов каждого подразделения."""
    departments = Department.objects.annotate(
        department_name=F("name"),
        expense_count=Count("expenses"),
        total_amount=Coalesce(
            Sum("expenses__amount"), ZERO_AMOUNT,
            output_field=MONEY_OUTPUT_FIELD,
        ),
    ).order_by("-total_amount", "name").values(
        "department_name",
        "expense_count",
        "total_amount",
    )

    return render(
        request,
        "catalogs/department_list.html",
        {"departments": departments},
    )


def documents_page(request):
    """Показать документы и расходы, связанные с каждым документом."""
    documents = Document.objects.annotate(
        document_number=F("number"),
        expense_count=Count("expenses"),
        total_amount=Coalesce(
            Sum("expenses__amount"), ZERO_AMOUNT,
            output_field=MONEY_OUTPUT_FIELD,
        ),
    ).order_by("-total_amount", "number").values(
        "document_number",
        "expense_count",
        "total_amount",
    )

    return render(
        request,
        "catalogs/document_list.html",
        {"documents": documents},
    )
