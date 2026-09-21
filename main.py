from expenses import (
    add_expense,
    find_expenses,
    filter_by_category,
    sort_expenses,
    get_statistics
)
from storage import load_expenses, save_expenses
from utils import input_float, input_text


DATA_FILE = "data/expenses.json"


def show_expenses(expenses: list[dict]) -> None:
    """Вывести список расходов."""

    if not expenses:
        print("Расходов нет.")
        return

    for expense in expenses:
        print(
            f'#{expense["id"]} | '
            f'{expense["amount"]:.2f} руб. | '
            f'{expense["category"]} | '
            f'{expense["department"]} | '
            f'{expense["document"]}'
        )


def add_new_expense(expenses: list[dict]) -> None:
    """Получить данные нового расхода и добавить его."""

    amount = input_float("Введите сумму расхода: ")
    category = input_text("Введите категорию: ")
    department = input_text("Введите подразделение: ")
    document = input_text("Введите документ: ")

    add_expense(
        expenses,
        amount,
        category,
        department,
        document
    )

    save_expenses(DATA_FILE, expenses)

    print("Расход добавлен.")


def search_expenses(expenses: list[dict]) -> None:
    """Найти расходы по категории или подразделению."""

    query = input_text("Введите категорию или подразделение: ")

    result = find_expenses(expenses, query)

    show_expenses(result)


def show_category_expenses(expenses: list[dict]) -> None:
    """Показать расходы выбранной категории."""

    category = input_text("Введите категорию: ")

    result = filter_by_category(expenses, category)

    show_expenses(result)


def show_sorted_expenses(expenses: list[dict]) -> None:
    """Показать расходы, отсортированные по сумме."""

    result = sort_expenses(expenses)

    show_expenses(result)


def show_statistics(expenses: list[dict]) -> None:
    """Показать статистику расходов."""

    statistics = get_statistics(expenses)

    print(f'Количество расходов: {statistics["count"]}')
    print(f'Общая сумма: {statistics["total"]:.2f} руб.')
    print(f'Средняя сумма: {statistics["average"]:.2f} руб.')


def main() -> None:
    """Запустить основное меню программы."""

    expenses = load_expenses(DATA_FILE)

    while True:
        print("\n=== Система учета расходов организации ===")
        print("1. Показать расходы")
        print("2. Добавить расход")
        print("3. Найти расход")
        print("4. Фильтр по категории")
        print("5. Сортировка по сумме")
        print("6. Статистика")
        print("0. Выход")

        choice = input("Выберите действие: ")

        if choice == "1":
            show_expenses(expenses)

        elif choice == "2":
            add_new_expense(expenses)

        elif choice == "3":
            search_expenses(expenses)

        elif choice == "4":
            show_category_expenses(expenses)

        elif choice == "5":
            show_sorted_expenses(expenses)

        elif choice == "6":
            show_statistics(expenses)

        elif choice == "0":
            print("Программа завершена.")
            break

        else:
            print("Неверный пункт меню.")


if __name__ == "__main__":
    main()
