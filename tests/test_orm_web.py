"""Проверки пользовательских страниц и операций Django ORM в ПР9."""

from decimal import Decimal
from datetime import timedelta
from pathlib import Path

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models.deletion import ProtectedError
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from catalogs.models import Category, Department, Document
from expenses.models import Expense

PROJECT_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture
def sample_data():
    """Подготовить данные предметной области для одного теста."""
    Expense.objects.all().delete()
    Category.objects.all().delete()
    Department.objects.all().delete()
    Document.objects.all().delete()

    equipment = Category.objects.create(name="Оборудование")
    stationery = Category.objects.create(name="Канцелярия")
    empty_category = Category.objects.create(name="Без расходов")

    it = Department.objects.create(name="IT")
    accounting = Department.objects.create(name="Бухгалтерия")
    production = Department.objects.create(name="Производство")

    document_101 = Document.objects.create(number="Счет №101")
    document_102 = Document.objects.create(number="Счет №102")
    document_103 = Document.objects.create(number="Счет №103")

    today = timezone.localdate()
    first = Expense.objects.create(
        amount=Decimal("15000.00"),
        expense_date=today + timedelta(days=1),
        category=equipment,
        department=it,
        document=document_101,
    )
    second = Expense.objects.create(
        amount=Decimal("5000.00"),
        expense_date=today - timedelta(days=1),
        category=stationery,
        department=accounting,
        document=document_102,
    )
    third = Expense.objects.create(
        amount=Decimal("25000.00"),
        expense_date=today,
        category=equipment,
        department=production,
        document=document_103,
    )

    # Дополнительные записи нужны для проверки пагинации.
    for index in range(4, 14):
        Expense.objects.create(
            amount=Decimal(f"{index * 100}.00"),
            expense_date=today,
            category=stationery,
            department=accounting,
            document=document_102,
        )

    yield {
        "equipment": equipment,
        "stationery": stationery,
        "empty_category": empty_category,
        "it": it,
        "accounting": accounting,
        "production": production,
        "first": first,
        "second": second,
        "third": third,
    }

    Expense.objects.all().delete()
    Category.objects.all().delete()
    Department.objects.all().delete()
    Document.objects.all().delete()


def test_models_have_expected_relationships_and_admin_registration():
    assert admin.site.is_registered(Category)
    assert admin.site.is_registered(Department)
    assert admin.site.is_registered(Document)
    assert admin.site.is_registered(Expense)

    assert Expense._meta.get_field("category").remote_field.related_name == (
        "expenses"
    )
    assert Expense._meta.get_field("department").remote_field.related_name == (
        "expenses"
    )
    assert Expense._meta.get_field("document").remote_field.related_name == (
        "expenses"
    )


def test_expense_list_displays_related_orm_data(sample_data):
    response = Client().get("/expenses/", HTTP_HOST="localhost")
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "Оборудование" in content
    assert "IT" in content
    assert "Счет №101" in content
    assert "Django ORM" in content
    assert response.context["expense_count"] == 13


def test_expense_filters_by_amount_category_department_and_search(
    sample_data,
):
    response = Client().get(
        "/expenses/",
        {
            "min_amount": "20000",
            "category_id": sample_data["equipment"].pk,
            "department_id": sample_data["production"].pk,
            "q": "Оборудование",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    expenses = list(response.context["expenses"].object_list)
    assert expenses == [sample_data["third"]]


def test_expense_search_uses_related_document_field(sample_data):
    response = Client().get(
        "/expenses/?q=101",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    expenses = list(response.context["expenses"].object_list)
    assert expenses == [sample_data["first"]]


def test_expense_specific_document_search(sample_data):
    response = Client().get(
        "/expenses/?document=101",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    expenses = list(response.context["expenses"].object_list)
    assert expenses == [sample_data["first"]]


def test_expense_sorting_uses_allowed_fields(sample_data):
    response = Client().get(
        "/expenses/?sort=amount_asc",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    expenses = list(response.context["expenses"].object_list)
    assert expenses[0].amount == Decimal("400.00")

    # Неизвестный ключ сортировки заменяется безопасным значением по умолчанию.
    invalid_response = Client().get(
        "/expenses/?sort=some_unapproved_field",
        HTTP_HOST="localhost",
    )
    assert invalid_response.status_code == 200
    assert invalid_response.context["filters"]["sort"] == "amount_desc"


def test_expense_pagination_keeps_filters_and_sort(sample_data):
    response = Client().get(
        "/expenses/?min_amount=0&sort=amount_asc&page=2",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    page_obj = response.context["page_obj"]
    assert page_obj.number == 2
    assert page_obj.paginator.num_pages == 2
    content = response.content.decode("utf-8")
    assert "min_amount=0" in content
    assert "sort=amount_asc" in content

    invalid_page = Client().get(
        "/expenses/?page=not-a-number",
        HTTP_HOST="localhost",
    )
    assert invalid_page.status_code == 200
    assert invalid_page.context["page_obj"].number == 1


def test_expense_detail_uses_related_models_and_404(sample_data):
    client = Client()
    expense = sample_data["first"]
    response = client.get(expense.get_absolute_url(), HTTP_HOST="localhost")
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "Оборудование" in content
    assert "IT" in content
    assert "Счет №101" in content
    assert expense.slug in content

    legacy = client.get(
        f"/expenses/{expense.pk}/",
        HTTP_HOST="localhost",
    )
    assert legacy.status_code == 301
    assert legacy["Location"] == expense.get_absolute_url()

    missing = client.get("/expenses/999999/", HTTP_HOST="localhost")
    assert missing.status_code == 404
    missing_slug = client.get(
        "/expenses/not-existing-slug/",
        HTTP_HOST="localhost",
    )
    assert missing_slug.status_code == 404


def test_statistics_aggregate_and_group_related_expenses(sample_data):
    response = Client().get(
        "/expenses/statistics/?threshold=20000",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    summary = response.context["summary"]
    assert summary["expense_count"] == 13
    assert summary["total_amount"] == Decimal("53500.00")

    category_rows = list(response.context["category_statistics"])
    equipment_row = next(
        row for row in category_rows
        if row["category_name"] == "Оборудование"
    )
    assert equipment_row["expense_count"] == 2
    assert equipment_row["total_amount"] == Decimal("40000.00")

    zero_row = next(
        row for row in category_rows
        if row["category_name"] == "Без расходов"
    )
    assert zero_row["expense_count"] == 0
    assert zero_row["total_amount"] == Decimal("0.00")

    high_categories = list(response.context["high_spend_categories"])
    assert [row["category_name"] for row in high_categories] == [
        "Оборудование"
    ]


def test_statistics_handles_invalid_threshold(sample_data):
    response = Client().get(
        "/expenses/statistics/?threshold=not-a-number",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    assert "Введите корректную сумму." in response.content.decode("utf-8")
    assert response.context["threshold"] == "not-a-number"


def test_catalog_pages_include_aggregates_and_empty_categories(sample_data):
    client = Client()

    categories = client.get("/categories/", HTTP_HOST="localhost")
    assert categories.status_code == 200
    assert "Без расходов" in categories.content.decode("utf-8")
    assert list(categories.context["empty_categories"]) == [
        sample_data["empty_category"]
    ]

    departments = client.get("/departments/", HTTP_HOST="localhost")
    assert departments.status_code == 200
    assert "Бухгалтерия" in departments.content.decode("utf-8")

    documents = client.get("/documents/", HTTP_HOST="localhost")
    assert documents.status_code == 200
    assert "Счет №101" in documents.content.decode("utf-8")


def test_orm_crud_and_protected_foreign_keys(sample_data):
    category = sample_data["equipment"]
    department = sample_data["it"]
    document = sample_data["first"].document

    new_expense = Expense.objects.create(
        amount=Decimal("777.50"),
        category=category,
        department=department,
        document=document,
    )
    assert Expense.objects.filter(pk=new_expense.pk).exists()

    new_expense.amount = Decimal("888.25")
    new_expense.save(update_fields=["amount"])
    new_expense.refresh_from_db()
    assert new_expense.amount == Decimal("888.25")

    with pytest.raises(ProtectedError):
        category.delete()

    new_expense.delete()
    assert not Expense.objects.filter(pk=new_expense.pk).exists()


def test_expense_dates_statuses_and_queryset_manager(sample_data):
    first = sample_data["first"]
    second = sample_data["second"]

    Expense.objects.filter(pk=first.pk).update(
        status=Expense.Status.PAID
    )
    Expense.objects.filter(pk=second.pk).update(
        status=Expense.Status.CANCELLED
    )

    assert Expense.objects.paid().filter(pk=first.pk).exists()
    assert Expense.objects.cancelled().filter(pk=second.pk).exists()
    assert not Expense.objects.not_cancelled().filter(pk=second.pk).exists()
    assert Expense.objects.for_date(first.expense_date).filter(
        pk=first.pk
    ).exists()
    assert Expense.objects.for_period(
        first.expense_date, first.expense_date
    ).filter(pk=first.pk).exists()
    assert Expense.objects.above_amount(Decimal("10000.00")).filter(
        pk=first.pk
    ).exists()


def test_expense_list_filters_by_date_and_status(sample_data):
    first = sample_data["first"]
    response = Client().get(
        "/expenses/",
        {
            "status": Expense.Status.PENDING,
            "date_from": first.expense_date.isoformat(),
            "date_to": first.expense_date.isoformat(),
            "sort": "date_desc",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    expenses = list(response.context["expenses"].object_list)
    assert first in expenses
    assert all(
        item.status == Expense.Status.PENDING
        and item.expense_date == first.expense_date
        for item in expenses
    )
    assert response.context["filters"]["status"] == Expense.Status.PENDING


def test_expense_list_reports_invalid_date_range(sample_data):
    today = timezone.localdate()
    response = Client().get(
        "/expenses/",
        {
            "date_from": (today + timedelta(days=1)).isoformat(),
            "date_to": today.isoformat(),
        },
        HTTP_HOST="localhost",
    )
    assert response.status_code == 200
    assert (
        "Начальная дата не может быть позже конечной"
        in response.context["error"]
    )
    assert response.context["expense_count"] == 0


def test_generated_large_expense_flag_is_calculated_by_database(sample_data):
    expense = sample_data["first"]
    assert expense.is_large is True

    expense.amount = Decimal("9999.99")
    expense.save(update_fields=["amount"])
    expense.refresh_from_db()
    assert expense.is_large is False

    expense.amount = Decimal("10000.00")
    expense.save(update_fields=["amount"])
    expense.refresh_from_db()
    assert expense.is_large is True


def test_statistics_exclude_cancelled_expenses_from_amounts(sample_data):
    Expense.objects.filter(pk=sample_data["second"].pk).update(
        status=Expense.Status.CANCELLED
    )
    response = Client().get("/expenses/statistics/", HTTP_HOST="localhost")

    assert response.status_code == 200
    summary = response.context["summary"]
    assert summary["expense_count"] == 12
    assert summary["cancelled_count"] == 1
    assert summary["pending_count"] == 12
    assert summary["total_amount"] == Decimal("48500.00")


def test_admin_configuration_inlines_search_and_bulk_actions():
    category_admin = admin.site._registry[Category]
    department_admin = admin.site._registry[Department]
    document_admin = admin.site._registry[Document]
    expense_admin = admin.site._registry[Expense]

    assert category_admin.inlines
    assert department_admin.inlines
    assert document_admin.inlines
    assert expense_admin.list_editable == ("amount", "status")
    assert "status" in expense_admin.list_filter
    assert "category__name" in expense_admin.search_fields
    assert "document__number" in expense_admin.search_fields
    assert "mark_as_paid" in expense_admin.actions
    assert "cancel_expenses" in expense_admin.actions
    assert "return_to_pending" in expense_admin.actions
    assert "slug" in expense_admin.readonly_fields
    assert "is_large" in expense_admin.readonly_fields


def test_admin_changelists_and_catalog_inline_pages_load(sample_data):
    user_model = get_user_model()
    administrator = user_model.objects.create_superuser(
        username="pr10_admin",
        email="pr10-admin@example.test",
        password="safe-test-password-123",
    )
    client = Client()
    client.force_login(administrator)

    expense_list = client.get(
        reverse("admin:expenses_expense_changelist"),
        HTTP_HOST="localhost",
    )
    assert expense_list.status_code == 200
    assert "Ожидает обработки" in expense_list.content.decode("utf-8")

    category_page = client.get(
        reverse(
            "admin:catalogs_category_change",
            args=[sample_data["equipment"].pk],
        ),
        HTTP_HOST="localhost",
    )
    assert category_page.status_code == 200
    assert "Расход №" in category_page.content.decode("utf-8")


def test_select_related_reduces_queries_for_related_expense_data(sample_data):
    with CaptureQueriesContext(connection) as without_joins:
        expenses = list(Expense.objects.all())
        for expense in expenses:
            _ = expense.category.name
            _ = expense.department.name
            _ = expense.document.number

    with CaptureQueriesContext(connection) as with_joins:
        expenses = list(
            Expense.objects.select_related(
                "category", "department", "document"
            )
        )
        for expense in expenses:
            _ = expense.category.name
            _ = expense.department.name
            _ = expense.document.number

    assert len(with_joins) < len(without_joins)


def test_context_processor_supplies_site_summary(sample_data):
    response = Client().get("/", HTTP_HOST="localhost")
    assert response.status_code == 200
    assert response.context["site_name"] == (
        "Система учёта расходов организации"
    )
    assert response.context["site_expense_count"] == 13
    assert response.context["site_active_expense_count"] == 13


def test_old_sqlite_calls_are_not_used_in_django_views():
    view_files = (
        PROJECT_DIR / "homepage" / "views.py",
        PROJECT_DIR / "catalogs" / "views.py",
        PROJECT_DIR / "expenses" / "views.py",
    )

    for view_file in view_files:
        source = view_file.read_text(encoding="utf-8")
        assert "sqlite3" not in source
        assert ".execute(" not in source
        assert "get_connection" not in source
