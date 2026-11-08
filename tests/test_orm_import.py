"""Проверка переноса данных из исходной базы ПР7 в Django ORM."""

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

    # Повторный импорт не создаёт дубликаты.
    import_data()
    assert Expense.objects.count() == 3
    assert Category.objects.count() == 2
