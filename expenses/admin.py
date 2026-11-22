"""Регистрация расходов организации в административной панели."""

from django.contrib import admin

from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "amount",
        "category",
        "department",
        "document",
        "status",
    )
    list_filter = ("status", "category", "department", "document")
    search_fields = (
        "category__name",
        "department__name",
        "document__number",
        "comment",
    )
    list_select_related = ("category", "department", "document")
    ordering = ("-amount", "id")
