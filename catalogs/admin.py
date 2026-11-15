"""Настройка администрирования справочников и связанных расходов."""

from decimal import Decimal

from django.contrib import admin
from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce

from expenses.models import Expense
from .models import Category, Department, Document


MONEY_OUTPUT_FIELD = DecimalField(max_digits=14, decimal_places=2)
ZERO_AMOUNT = Value(Decimal("0.00"), output_field=MONEY_OUTPUT_FIELD)
ACTIVE_EXPENSES = ~Q(expenses__status=Expense.Status.CANCELLED)


class ExpenseInlineBase(admin.TabularInline):
    """Только для чтения показывает расходы внутри карточки справочника."""

    model = Expense
    extra = 0
    can_delete = False
    show_change_link = True
    readonly_fields = ()

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "category", "department", "document"
        )


class CategoryExpenseInline(ExpenseInlineBase):
    fields = (
        "id",
        "expense_date",
        "amount",
        "department",
        "document",
        "status",
    )
    readonly_fields = fields


class DepartmentExpenseInline(ExpenseInlineBase):
    fields = (
        "id",
        "expense_date",
        "amount",
        "category",
        "document",
        "status",
    )
    readonly_fields = fields


class DocumentExpenseInline(ExpenseInlineBase):
    fields = (
        "id",
        "expense_date",
        "amount",
        "category",
        "department",
        "status",
    )
    readonly_fields = fields


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "expenses_count", "expenses_total")
    list_display_links = ("id",)
    list_editable = ("name",)
    search_fields = ("name",)
    ordering = ("name",)
    list_per_page = 25
    inlines = (CategoryExpenseInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _expenses_count=Count("expenses", filter=ACTIVE_EXPENSES),
            _expenses_total=Coalesce(
                Sum("expenses__amount", filter=ACTIVE_EXPENSES),
                ZERO_AMOUNT,
                output_field=MONEY_OUTPUT_FIELD,
            ),
        )

    @admin.display(description="Расходов", ordering="_expenses_count")
    def expenses_count(self, obj):
        return obj._expenses_count

    @admin.display(description="Сумма, ₽", ordering="_expenses_total")
    def expenses_total(self, obj):
        return obj._expenses_total


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "expenses_count", "expenses_total")
    list_display_links = ("id",)
    list_editable = ("name",)
    search_fields = ("name",)
    ordering = ("name",)
    list_per_page = 25
    inlines = (DepartmentExpenseInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _expenses_count=Count("expenses", filter=ACTIVE_EXPENSES),
            _expenses_total=Coalesce(
                Sum("expenses__amount", filter=ACTIVE_EXPENSES),
                ZERO_AMOUNT,
                output_field=MONEY_OUTPUT_FIELD,
            ),
        )

    @admin.display(description="Расходов", ordering="_expenses_count")
    def expenses_count(self, obj):
        return obj._expenses_count

    @admin.display(description="Сумма, ₽", ordering="_expenses_total")
    def expenses_total(self, obj):
        return obj._expenses_total


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "number", "expenses_count", "expenses_total")
    list_display_links = ("id",)
    list_editable = ("number",)
    search_fields = ("number",)
    ordering = ("number",)
    list_per_page = 25
    inlines = (DocumentExpenseInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _expenses_count=Count("expenses", filter=ACTIVE_EXPENSES),
            _expenses_total=Coalesce(
                Sum("expenses__amount", filter=ACTIVE_EXPENSES),
                ZERO_AMOUNT,
                output_field=MONEY_OUTPUT_FIELD,
            ),
        )

    @admin.display(description="Расходов", ordering="_expenses_count")
    def expenses_count(self, obj):
        return obj._expenses_count

    @admin.display(description="Сумма, ₽", ordering="_expenses_total")
    def expenses_total(self, obj):
        return obj._expenses_total
