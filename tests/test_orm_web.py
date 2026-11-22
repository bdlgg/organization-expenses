"""Проверки пользовательских страниц и операций Django ORM в ПР11."""

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

    # Неизвестная сортировка заменяется безопасным значением по умолчанию.
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
        sample_data["first"].get_absolute_url(),
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


def test_expense_create_form_saves_only_validated_data(sample_data):
    client = Client()
    payload = {
        "amount": "1234.56",
        "category": sample_data["equipment"].pk,
        "department": sample_data["it"].pk,
        "document": sample_data["first"].document_id,
        "comment": "Покупка монитора",
    }

    response = client.post("/expenses/new/", payload, HTTP_HOST="localhost")

    assert response.status_code == 302
    created = Expense.objects.get(amount=Decimal("1234.56"))
    assert created.comment == "Покупка монитора"
    assert created.status == Expense.STATUS_PENDING
    assert created.slug


def test_expense_create_form_shows_validation_error_without_saving(
    sample_data,
):
    before_count = Expense.objects.count()
    response = Client().post(
        "/expenses/new/",
        {
            "amount": "-10.00",
            "category": sample_data["equipment"].pk,
            "department": sample_data["it"].pk,
            "document": sample_data["first"].document_id,
            "comment": "Некорректная сумма",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    assert (
        "Сумма расхода должна быть больше нуля."
        in response.content.decode("utf-8")
    )
    assert Expense.objects.count() == before_count


def test_expense_update_form_uses_instance_and_preserves_status(sample_data):
    expense = sample_data["first"]
    expense.status = Expense.STATUS_APPROVED
    expense.save(update_fields=["status"])

    client = Client()
    page = client.get(
        f"/expenses/{expense.slug}/edit/",
        HTTP_HOST="localhost",
    )
    assert page.status_code == 200
    assert "Редактирование расхода" in page.content.decode("utf-8")

    response = client.post(
        f"/expenses/{expense.slug}/edit/",
        {
            "amount": "16000.00",
            "category": expense.category_id,
            "department": expense.department_id,
            "document": expense.document_id,
            "comment": "Изменённый комментарий",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    expense.refresh_from_db()
    assert expense.amount == Decimal("16000.00")
    assert expense.comment == "Изменённый комментарий"
    assert expense.status == Expense.STATUS_APPROVED


def test_edit_missing_expense_returns_404():
    response = Client().get(
        "/expenses/absent-expense/edit/",
        HTTP_HOST="localhost",
    )
    assert response.status_code == 404


def test_status_changes_only_with_post_and_valid_transition(sample_data):
    expense = sample_data["first"]
    client = Client()
    status_url = f"/expenses/{expense.slug}/status/"

    get_response = client.get(status_url, HTTP_HOST="localhost")
    assert get_response.status_code == 405

    post_response = client.post(
        status_url,
        {"status": Expense.STATUS_CANCELLED},
        HTTP_HOST="localhost",
    )
    assert post_response.status_code == 302
    expense.refresh_from_db()
    assert expense.status == Expense.STATUS_CANCELLED

    invalid_response = client.post(
        status_url,
        {"status": Expense.STATUS_PAID},
        HTTP_HOST="localhost",
    )
    assert invalid_response.status_code == 400
    expense.refresh_from_db()
    assert expense.status == Expense.STATUS_CANCELLED


def test_status_form_requires_csrf_token(sample_data):
    expense = sample_data["first"]
    client = Client(enforce_csrf_checks=True)
    detail = client.get(
        expense.get_absolute_url(),
        HTTP_HOST="localhost",
    )
    assert detail.status_code == 200
    assert b"csrfmiddlewaretoken" in detail.content

    response = client.post(
        f"/expenses/{expense.slug}/status/",
        {"status": Expense.STATUS_CANCELLED},
        HTTP_HOST="localhost",
    )
    assert response.status_code == 403


def test_expense_create_uploads_and_displays_receipt_image(
    sample_data, tmp_path,
):
    from io import BytesIO

    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.test import override_settings
    from PIL import Image

    image_buffer = BytesIO()
    Image.new("RGB", (3, 3), color="white").save(image_buffer, format="PNG")
    upload = SimpleUploadedFile(
        "receipt.png",
        image_buffer.getvalue(),
        content_type="image/png",
    )

    with override_settings(MEDIA_ROOT=tmp_path):
        response = Client().post(
            "/expenses/new/",
            {
                "amount": "999.99",
                "category": sample_data["equipment"].pk,
                "department": sample_data["it"].pk,
                "document": sample_data["first"].document_id,
                "comment": "Оплата по счёту",
                "receipt_image": upload,
            },
            HTTP_HOST="localhost",
        )

        assert response.status_code == 302
        created = Expense.objects.get(amount=Decimal("999.99"))
        assert created.receipt_image.name.startswith("receipts/")
        assert created.receipt_image.storage.exists(created.receipt_image.name)

        detail = Client().get(
            created.get_absolute_url(),
            HTTP_HOST="localhost",
        )
        assert detail.status_code == 200
        assert "Подтверждающий документ" in detail.content.decode("utf-8")


def test_expense_filter_form_handles_invalid_get_values(sample_data):
    response = Client().get(
        "/expenses/?min_amount=not-a-number&category_id=bad&sort=unknown",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Введите корректную сумму." in content
    assert response.context["filters"]["sort"] == "amount_desc"


def test_expense_rejects_unsupported_receipt_image_format(sample_data):
    from io import BytesIO

    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image

    image_buffer = BytesIO()
    Image.new("RGB", (3, 3), color="white").save(image_buffer, format="GIF")
    upload = SimpleUploadedFile(
        "receipt.gif",
        image_buffer.getvalue(),
        content_type="image/gif",
    )
    before_count = Expense.objects.count()

    response = Client().post(
        "/expenses/new/",
        {
            "amount": "100.00",
            "category": sample_data["equipment"].pk,
            "department": sample_data["it"].pk,
            "document": sample_data["first"].document_id,
            "receipt_image": upload,
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    assert "Разрешены только изображения JPG, PNG и WebP." in (
        response.content.decode("utf-8")
    )
    assert Expense.objects.count() == before_count
