from expenses import (
    add_expense,
    find_expenses,
    calculate_total,
    sort_expenses
)


def test_add_expense():
    expenses = []

    add_expense(
        expenses,
        1000,
        "Оборудование",
        "IT",
        "Счет №1"
    )

    assert len(expenses) == 1
    assert expenses[0]["amount"] == 1000


def test_find_expenses():
    expenses = [
        {
            "id": 1,
            "amount": 1000,
            "category": "Оборудование",
            "department": "IT",
            "document": "Счет №1"
        }
    ]

    result = find_expenses(expenses, "IT")

    assert len(result) == 1


def test_calculate_total():
    expenses = [
        {"amount": 1000},
        {"amount": 2000},
        {"amount": 3000}
    ]

    assert calculate_total(expenses) == 6000


def test_sort_expenses():
    expenses = [
        {"amount": 3000},
        {"amount": 1000},
        {"amount": 2000}
    ]

    result = sort_expenses(expenses)

    assert result[0]["amount"] == 1000
    assert result[-1]["amount"] == 3000