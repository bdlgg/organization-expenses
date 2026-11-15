"""Проверка переноса данных из исходной базы ПР7 в Django ORM."""

from datetime import date

import pytest

from catalogs.models import Category, Department, Document
from db.import_sqlite_to_orm import import_data
from expenses.models import Expense


@pytest.mark.usefixtures("django_test_database")
def test_import_preserves_identifiers_and_relationships():
    import_data()

    assert Category.objects.count() == 2
    assert Department.objects.count() == 3
    assert Document.objects.count() == 3
    assert Expense.objects.count() == 3

    expense = Expense.objects.select_related(
        "category",
        "department",
        "document",
    ).get(pk=1)
    assert expense.category.name == "Оборудование"
    assert expense.department.name == "IT"
    assert expense.document.number == "Счет №101"
    assert expense.slug
    assert expense.status == Expense.Status.PENDING
    assert expense.expense_date is None

    # Дата и статус, добавленные после перехода на ORM, должны сохраниться.
    expense.expense_date = date(2026, 1, 15)
    expense.status = Expense.Status.PAID
    expense.save(update_fields=["expense_date", "status"])

    # Повторный импорт не создаёт дубликаты и не стирает поля ПР10.
    import_data()
    assert Expense.objects.count() == 3
    assert Category.objects.count() == 2
    expense.refresh_from_db()
    assert expense.expense_date == date(2026, 1, 15)
    assert expense.status == Expense.Status.PAID
