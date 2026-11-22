"""Представления реестра расходов, форм и финансовой статистики."""

from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Avg, Count, F, Max, Min, Q, Sum, Value
from django.db.models.fields import DecimalField
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalogs.models import Category, Department
from .forms import (
    ExpenseFilterForm,
    ExpenseForm,
    ExpenseStatusForm,
    ExpenseThresholdForm,
)
from .models import Expense


PAGE_SIZE = 10
DEFAULT_SORT = "amount_desc"
SORT_OPTIONS = {
    "amount_desc": "-amount",
    "amount_asc": "amount",
    "category": "category__name",
    "department": "department__name",
}
ZERO_AMOUNT = Value(
    Decimal("0.00"),
    output_field=DecimalField(max_digits=12, decimal_places=2),
)


def _ensure_expense_slug(expense):
    """Создать адрес для ранее импортированной записи без slug."""
    if not expense.slug:
        expense.slug = f"expense-{expense.pk}"
        expense.save(update_fields=["slug"])


def expense_list(request):
    """Показать расходы с проверенной Django Form фильтрацией."""
    form = ExpenseFilterForm(request.GET, initial={"sort": DEFAULT_SORT})
    form.is_valid()
    cleaned = form.cleaned_data

    expenses = Expense.objects.select_related(
        "category",
        "department",
        "document",
    )

    min_amount = cleaned.get("min_amount")
    if min_amount is not None:
        expenses = expenses.filter(amount__gte=min_amount)

    category = cleaned.get("category_id")
    if category is not None:
        expenses = expenses.filter(category=category)

    department = cleaned.get("department_id")
    if department is not None:
        expenses = expenses.filter(department=department)

    search_text = cleaned.get("q", "")
    if search_text:
        expenses = expenses.filter(
            Q(category__name__icontains=search_text)
            | Q(department__name__icontains=search_text)
            | Q(document__number__icontains=search_text)
            | Q(comment__icontains=search_text)
        )

    document_number = cleaned.get("document", "")
    if document_number:
        expenses = expenses.filter(
            document__number__icontains=document_number
        )

    sort_key = cleaned.get("sort") or DEFAULT_SORT
    if sort_key not in SORT_OPTIONS:
        sort_key = DEFAULT_SORT
    expenses = expenses.order_by(SORT_OPTIONS[sort_key], "pk")

    paginator = Paginator(expenses, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))

    for expense in page_obj.object_list:
        _ensure_expense_slug(expense)

    query_params = request.GET.copy()
    query_params.pop("page", None)

    context = {
        "expenses": page_obj,
        "page_obj": page_obj,
        "form": form,
        "expense_count": paginator.count,
        "filters": {
            "min_amount": request.GET.get("min_amount", ""),
            "category_id": request.GET.get("category_id", ""),
            "department_id": request.GET.get("department_id", ""),
            "q": request.GET.get("q", ""),
            "document": request.GET.get("document", ""),
            "sort": sort_key,
        },
        "query_string": query_params.urlencode(),
    }
    return render(request, "expenses/expense_list.html", context)


def expense_create(request):
    """Создать расход после успешной проверки ModelForm."""
    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save()
            return redirect("expenses:expense_detail", slug=expense.slug)
    else:
        form = ExpenseForm()

    return render(
        request,
        "expenses/expense_form.html",
        {
            "form": form,
            "page_title": "Добавление расхода",
            "submit_label": "Создать расход",
        },
    )


def expense_update(request, slug):
    """Изменить существующий расход через ModelForm и параметр instance."""
    expense = get_object_or_404(Expense, slug=slug)

    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            updated_expense = form.save()
            return redirect(
                "expenses:expense_detail",
                slug=updated_expense.slug,
            )
    else:
        form = ExpenseForm(instance=expense)

    return render(
        request,
        "expenses/expense_form.html",
        {
            "form": form,
            "expense": expense,
            "page_title": f"Редактирование расхода №{expense.pk}",
            "submit_label": "Сохранить изменения",
        },
    )


def expense_detail(request, slug):
    """Показать карточку расхода и допустимые действия со статусом."""
    expense = get_object_or_404(
        Expense.objects.select_related("category", "department", "document"),
        slug=slug,
    )
    status_form = ExpenseStatusForm(expense=expense)
    return render(
        request,
        "expenses/expense_detail.html",
        {"expense": expense, "status_form": status_form},
    )


def expense_detail_legacy(request, expense_id):
    """Сохранить прежние числовые адреса карточек расходов."""
    expense = get_object_or_404(Expense, pk=expense_id)
    _ensure_expense_slug(expense)
    return redirect(
        "expenses:expense_detail",
        slug=expense.slug,
        permanent=True,
    )


@require_POST
def expense_change_status(request, slug):
    """Изменить статус расхода только проверенным POST-запросом."""
    expense = get_object_or_404(Expense, slug=slug)
    form = ExpenseStatusForm(request.POST, expense=expense)

    if form.is_valid():
        expense.status = form.cleaned_data["status"]
        expense.save(update_fields=["status"])
        return redirect("expenses:expense_detail", slug=expense.slug)

    return render(
        request,
        "expenses/expense_detail.html",
        {"expense": expense, "status_form": form},
        status=400,
    )


def expense_statistics(request):
    """Показать агрегированную статистику с проверкой GET-порога через Form."""
    has_threshold = "threshold" in request.GET
    form = ExpenseThresholdForm(
        request.GET if has_threshold else None,
        initial={"threshold": Decimal("10000.00")},
    )
    form_is_valid = form.is_valid() if form.is_bound else True
    threshold = (
        form.cleaned_data.get("threshold")
        if form.is_bound and form_is_valid
        else Decimal("10000.00")
    )
    if threshold is None:
        threshold = Decimal("10000.00")

    summary = Expense.objects.aggregate(
        expense_count=Count("pk"),
        total_amount=Coalesce(Sum("amount"), ZERO_AMOUNT),
        average_amount=Coalesce(Avg("amount"), ZERO_AMOUNT),
        min_amount=Min("amount"),
        max_amount=Max("amount"),
    )

    category_statistics = (
        Category.objects.annotate(
            category_name=F("name"),
            expense_count=Count("expenses"),
            total_amount=Coalesce(Sum("expenses__amount"), ZERO_AMOUNT),
        )
        .values("category_name", "expense_count", "total_amount")
        .order_by("-total_amount", "category_name")
    )
    department_statistics = (
        Department.objects.annotate(
            department_name=F("name"),
            expense_count=Count("expenses"),
            total_amount=Coalesce(Sum("expenses__amount"), ZERO_AMOUNT),
        )
        .values("department_name", "expense_count", "total_amount")
        .order_by("-total_amount", "department_name")
    )
    high_spend_categories = (
        Category.objects.annotate(
            category_name=F("name"),
            expense_count=Count("expenses"),
            total_amount=Sum("expenses__amount"),
        )
        .filter(total_amount__gt=threshold)
        .values("category_name", "expense_count", "total_amount")
        .order_by("-total_amount", "category_name")
    )

    raw_threshold = request.GET.get("threshold", "10000")
    error = ""
    if form.is_bound and not form_is_valid:
        error = "Введите корректную сумму."

    return render(
        request,
        "expenses/expense_statistics.html",
        {
            "summary": summary,
            "category_statistics": category_statistics,
            "department_statistics": department_statistics,
            "high_spend_categories": high_spend_categories,
            "form": form,
            "threshold": raw_threshold,
            "error": error,
        },
    )
