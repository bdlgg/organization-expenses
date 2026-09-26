from categories import Category
from departments import Department
from documents import Document
from expenses import (
    Expense,
    add_expense,
    calculate_total,
    find_expenses,
    sort_expenses
)


def test_add_expense():
    expenses = []

    category = Category("Оборудование")
    department = Department("IT")
    document = Document("Счет №1")

    expense = add_expense(
        expenses,
        1000,
        category,
        department,
        document
    )

    assert len(expenses) == 1
    assert expense.amount == 1000
    assert expense.category.name == "Оборудование"


def test_find_expenses():
    expenses = [
        Expense(
            1,
            1000,
            Category("Оборудование"),
            Department("IT"),
            Document("Счет №1")
        )
    ]

    result = find_expenses(
        expenses,
        "IT"
    )

    assert len(result) == 1


def test_calculate_total():
    expenses = [
        Expense(
            1,
            1000,
            Category("Оборудование"),
            Department("IT"),
            Document("Счет №1")
        ),
        Expense(
            2,
            2000,
            Category("Канцелярия"),
            Department("IT"),
            Document("Счет №2")
        )
    ]

    assert calculate_total(expenses) == 3000


def test_sort_expenses():
    expenses = [
        Expense(
            1,
            3000,
            Category("Оборудование"),
            Department("IT"),
            Document("Счет №3")
        ),
        Expense(
            2,
            1000,
            Category("Канцелярия"),
            Department("IT"),
            Document("Счет №1")
        )
    ]

    result = sort_expenses(expenses)

    assert result[0].amount == 1000
    assert result[-1].amount == 3000