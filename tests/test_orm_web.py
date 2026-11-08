"""Проверки пользовательских страниц и операций Django ORM в ПР9."""

from decimal import Decimal
from pathlib import Path

import pytest
from django.contrib import admin
from django.db.models.deletion import ProtectedError
from django.test import Client

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

    first = Expense.objects.create(
        amount=Decimal("15000.00"),
        category=equipment,
        department=it,
        document=document_101,
    )
    second = Expense.objects.create(
        amount=Decimal("5000.00"),
        category=stationery,
        department=accounting,
        document=document_102,
    )
    third = Expense.objects.create(
        amount=Decimal("25000.00"),
        category=equipment,
        department=production,
        document=document_103,
    )

    # Дополнительные записи нужны для проверки пагинации.
    for index in range(4, 14):
        Expense.objects.create(
            amount=Decimal(f"{index * 100}.00"),
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
    assert "Данные и фильтры обрабатываются средствами Django ORM" in content
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
    response = client.get(
        f"/expenses/{sample_data['first'].pk}/",
        HTTP_HOST="localhost",
    )
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "Оборудование" in content
    assert "IT" in content
    assert "Счет №101" in content

    missing = client.get("/expenses/999999/", HTTP_HOST="localhost")
    assert missing.status_code == 404


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
