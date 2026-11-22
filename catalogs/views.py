"""Представления справочников с агрегатами, полученными через Django ORM."""

from decimal import Decimal

from django.db.models import Count, F, Sum, Value
from django.db.models.fields import DecimalField
from django.db.models.functions import Coalesce
from django.shortcuts import render

from .models import Category, Department, Document


ZERO_AMOUNT = Value(
    Decimal("0.00"),
    output_field=DecimalField(max_digits=12, decimal_places=2),
)


def categories_page(request):
    """Показать категории и количество/сумму связанных расходов."""
    categories = Category.objects.annotate(
        category_name=F("name"),
        expense_count=Count("expenses"),
        total_amount=Coalesce(Sum("expenses__amount"), ZERO_AMOUNT),
    ).order_by("name")
    empty_categories = Category.objects.annotate(
        expense_count=Count("expenses")
    ).filter(expense_count=0)
    return render(
        request,
        "catalogs/category_list.html",
        {
            "categories": categories,
            "empty_categories": empty_categories,
        },
    )


def departments_page(request):
    """Показать подразделения и суммы учтённых расходов."""
    departments = Department.objects.annotate(
        department_name=F("name"),
        expense_count=Count("expenses"),
        total_amount=Coalesce(Sum("expenses__amount"), ZERO_AMOUNT),
    ).order_by("name")
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
        total_amount=Coalesce(Sum("expenses__amount"), ZERO_AMOUNT),
    ).order_by("number")
    return render(
        request,
        "catalogs/document_list.html",
        {"documents": documents},
    )
