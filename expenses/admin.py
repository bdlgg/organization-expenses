"""Регистрация расходов в административной панели Django."""

from django.contrib import admin

from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("id", "amount", "category", "department", "document")
    list_filter = ("category", "department", "document")
    search_fields = (
        "category__name",
        "department__name",
        "document__number",
    )
    list_select_related = ("category", "department", "document")
    ordering = ("-amount", "id")
