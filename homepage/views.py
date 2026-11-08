"""Представления главной страницы и страницы 404."""

from decimal import Decimal

from django.db.models import Avg, Count, DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import render

from expenses.models import Expense


MONEY_OUTPUT_FIELD = DecimalField(max_digits=14, decimal_places=2)
ZERO_AMOUNT = Value(Decimal("0.00"), output_field=MONEY_OUTPUT_FIELD)


def index(request):
    """Показать краткую сводку расходов, рассчитанную средствами ORM."""
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
    )

    return render(request, "homepage/index.html", {"summary": summary})


def page_not_found(request, exception):
    """Вернуть оформленную страницу 404 для неизвестного URL."""
    return render(request, "homepage/404.html", status=404)
