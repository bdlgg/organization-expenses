from typing import List

from models import Expense
from storage import (
    load_categories,
    load_departments,
    load_documents,
    load_expenses,
    save_categories,
    save_departments,
    save_documents,
    save_expenses,
)


DATA_DIR = "data"

CATEGORIES_FILE = f"{DATA_DIR}/categories.json"
DEPARTMENTS_FILE = f"{DATA_DIR}/departments.json"
DOCUMENTS_FILE = f"{DATA_DIR}/documents.json"
EXPENSES_FILE = f"{DATA_DIR}/expenses.json"


def print_expenses(expenses: List[Expense]) -> None:
    """Вывести расходы."""

    if not expenses:
        print("Расходы отсутствуют.")
        return

    for expense in expenses:
        print(expense)


def main() -> None:
    """Запустить приложение."""

    categories = load_categories(CATEGORIES_FILE)
    departments = load_departments(DEPARTMENTS_FILE)
    documents = load_documents(DOCUMENTS_FILE)

    expenses = load_expenses(
        EXPENSES_FILE,
        categories,
        departments,
        documents,
    )

    print("Система учета расходов организации")
    print()

    print("Расходы:")
    print_expenses(expenses)

    print()
    print(f"Количество расходов: {len(expenses)}")

    total = sum(expense.amount for expense in expenses)
    print(f"Общая сумма: {total:.2f} руб.")

    save_categories(CATEGORIES_FILE, categories)
    save_departments(DEPARTMENTS_FILE, departments)
    save_documents(DOCUMENTS_FILE, documents)
    save_expenses(EXPENSES_FILE, expenses)


if __name__ == "__main__":
    main()
