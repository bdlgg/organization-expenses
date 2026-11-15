"""Общие сведения о проекте для всех шаблонов сайта."""

from django.db.models import Count, Q


def expense_summary(request):
    """Передать название сайта и компактную сводку расходов в шаблоны."""
    # Импорт внутри функции предотвращает циклическую зависимость при старте.
    from expenses.models import Expense

    summary = Expense.objects.aggregate(
        total=Count("pk"),
        not_cancelled=Count(
            "pk",
            filter=~Q(status=Expense.Status.CANCELLED),
        ),
    )
    return {
        "site_name": "Система учёта расходов организации",
        "site_expense_count": summary["total"],
        "site_active_expense_count": summary["not_cancelled"],
    }
