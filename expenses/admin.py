"""Настройка управления расходами в административной панели Django."""

from django.contrib import admin, messages
from django.db.models import F

from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "expense_date",
        "amount",
        "category",
        "department",
        "document",
        "status",
        "is_large",
    )
    list_display_links = ("id",)
    list_editable = ("amount", "status")
    list_filter = (
        "status",
        "expense_date",
        "category",
        "department",
        "is_large",
    )
    search_fields = (
        "slug",
        "category__name",
        "department__name",
        "document__number",
    )
    list_select_related = ("category", "department", "document")
    autocomplete_fields = ("category", "department", "document")
    ordering = (F("expense_date").desc(nulls_last=True), "-pk")
    date_hierarchy = "expense_date"
    list_per_page = 25
    save_on_top = True
    readonly_fields = ("id", "slug", "is_large")
    fields = (
        "id",
        "expense_date",
        "amount",
        "category",
        "department",
        "document",
        "status",
        "is_large",
        "slug",
    )
    actions = ("mark_as_paid", "cancel_expenses", "return_to_pending")

    @admin.action(description="Отметить выбранные расходы как оплаченные")
    def mark_as_paid(self, request, queryset):
        updated = queryset.exclude(
            status=Expense.Status.CANCELLED
        ).update(status=Expense.Status.PAID)
        self.message_user(
            request,
            f"Оплачено расходов: {updated}.",
            messages.SUCCESS,
        )

    @admin.action(description="Отменить выбранные расходы")
    def cancel_expenses(self, request, queryset):
        updated = queryset.exclude(
            status=Expense.Status.CANCELLED
        ).update(status=Expense.Status.CANCELLED)
        self.message_user(
            request,
            f"Отменено расходов: {updated}.",
            messages.SUCCESS,
        )

    @admin.action(description="Вернуть выбранные расходы в обработку")
    def return_to_pending(self, request, queryset):
        updated = queryset.update(status=Expense.Status.PENDING)
        self.message_user(
            request,
            f"Возвращено в обработку расходов: {updated}.",
            messages.SUCCESS,
        )


admin.site.site_header = "Управление расходами организации"
admin.site.site_title = "Администрирование расходов"
admin.site.index_title = "Справочники и учёт расходов"
