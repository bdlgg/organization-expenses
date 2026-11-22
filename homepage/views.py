"""Представления главной страницы и страницы 404."""

from decimal import Decimal

from django.db.models import Avg, Count, Sum, Value
from django.db.models.fields import DecimalField
from django.db.models.functions import Coalesce
from django.shortcuts import render

from expenses.models import Expense


ZERO_AMOUNT = Value(
    Decimal("0.00"),
    output_field=DecimalField(max_digits=12, decimal_places=2),
)


def index(request):
    """Показать сводку расходов, рассчитанную средствами Django ORM."""
    summary = Expense.objects.aggregate(
        expense_count=Count("pk"),
        total_amount=Coalesce(Sum("amount"), ZERO_AMOUNT),
        average_amount=Coalesce(Avg("amount"), ZERO_AMOUNT),
    )
    return render(request, "homepage/index.html", {"summary": summary})


def page_not_found(request, exception):
    """Вернуть оформленную страницу 404 для неизвестного URL."""
    return render(request, "homepage/404.html", status=404)
