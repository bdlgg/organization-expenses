from typing import List

from categories import (
    Category,
    add_category,
    find_category
)
from departments import (
    Department,
    add_department,
    find_department
)
from documents import (
    Document,
    add_document,
    find_document
)
from expenses import (
    Expense,
    add_expense,
    find_expenses,
    filter_by_category,
    sort_expenses,
    get_statistics
)
from storage import (
    load_expenses,
    save_expenses,
    load_categories,
    save_categories,
    load_departments,
    save_departments,
    load_documents,
    save_documents
)
from utils import input_float, input_int, input_text


EXPENSES_FILE = "data/expenses.json"
CATEGORIES_FILE = "data/categories.json"
DEPARTMENTS_FILE = "data/departments.json"
DOCUMENTS_FILE = "data/documents.json"


def show_expenses(expenses: List[Expense]) -> None:
    """Вывести список расходов."""

    if not expenses:
        print("Расходов нет.")
        return

    for expense in expenses:
        print(expense.get_info())


def add_new_expense(
    expenses: List[Expense],
    categories: List[Category],
    departments: List[Department],
    documents: List[Document]
) -> None:
    """Получить данные и добавить новый расход."""

    amount = input_float("Введите сумму расхода: ")
    category_name = input_text("Введите категорию: ")
    department_name = input_text("Введите подразделение: ")
    document_number = input_text("Введите документ: ")

    category = find_category(
        categories,
        category_name
    )

    if category is None:
        category = Category(category_name)
        add_category(categories, category)

    department = find_department(
        departments,
        department_name
    )

    if department is None:
        department = Department(department_name)
        add_department(
            departments,
            department
        )

    document = find_document(
        documents,
        document_number
    )

    if document is None:
        document = Document(document_number)
        add_document(documents, document)

    add_expense(
        expenses,
        amount,
        category,
        department,
        document
    )

    save_expenses(EXPENSES_FILE, expenses)
    save_categories(CATEGORIES_FILE, categories)
    save_departments(DEPARTMENTS_FILE, departments)
    save_documents(DOCUMENTS_FILE, documents)

    print("Расход добавлен.")


def search_expenses(
    expenses: List[Expense]
) -> None:
    """Найти расходы по категории, подразделению или документу."""

    query = input_text("Введите поисковый запрос: ")

    result = find_expenses(
        expenses,
        query
    )

    show_expenses(result)


def show_category_expenses(
    expenses: List[Expense]
) -> None:
    """Показать расходы выбранной категории."""

    category = input_text("Введите категорию: ")

    result = filter_by_category(
        expenses,
        category
    )

    show_expenses(result)


def show_sorted_expenses(
    expenses: List[Expense]
) -> None:
    """Показать расходы, отсортированные по сумме."""

    result = sort_expenses(expenses)

    show_expenses(result)


def show_statistics(
    expenses: List[Expense]
) -> None:
    """Показать статистику расходов."""

    statistics = get_statistics(expenses)

    print(
        f'Количество расходов: '
        f'{statistics["count"]}'
    )
    print(
        f'Общая сумма: '
        f'{statistics["total"]:.2f} руб.'
    )
    print(
        f'Средняя сумма: '
        f'{statistics["average"]:.2f} руб.'
    )


def main() -> None:
    """Запустить основное меню программы."""

    expenses = load_expenses(EXPENSES_FILE)
    categories = load_categories(CATEGORIES_FILE)
    departments = load_departments(DEPARTMENTS_FILE)
    documents = load_documents(DOCUMENTS_FILE)

    while True:
        print(
            "\n=== Система учета расходов организации ==="
        )
        print("1. Показать расходы")
        print("2. Добавить расход")
        print("3. Найти расход")
        print("4. Фильтр по категории")
        print("5. Сортировка по сумме")
        print("6. Статистика")
        print("0. Выход")

        choice = input_int("Выберите действие: ")

        if choice == 1:
            show_expenses(expenses)

        elif choice == 2:
            add_new_expense(
                expenses,
                categories,
                departments,
                documents
            )

        elif choice == 3:
            search_expenses(expenses)

        elif choice == 4:
            show_category_expenses(expenses)

        elif choice == 5:
            show_sorted_expenses(expenses)

        elif choice == 6:
            show_statistics(expenses)

        elif choice == 0:
            print("Программа завершена.")
            break

        else:
            print("Неверный пункт меню.")


if __name__ == "__main__":
    main()