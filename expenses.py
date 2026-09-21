def add_expense(
    expenses: list[dict],
    amount: float,
    category: str,
    department: str,
    document: str
) -> None:
    """Добавить новый расход в список."""

    expense_id = len(expenses) + 1

    expense = {
        "id": expense_id,
        "amount": amount,
        "category": category,
        "department": department,
        "document": document
    }

    expenses.append(expense)


def find_expenses(
    expenses: list[dict],
    query: str
) -> list[dict]:
    """Найти расходы по категории или подразделению."""

    result = []

    for expense in expenses:
        if (
            query.lower() in expense["category"].lower()
            or query.lower() in expense["department"].lower()
        ):
            result.append(expense)

    return result


def filter_by_category(
    expenses: list[dict],
    category: str
) -> list[dict]:
    """Отобрать расходы по категории."""

    return [
        expense
        for expense in expenses
        if expense["category"].lower() == category.lower()
    ]


def sort_expenses(
    expenses: list[dict]
) -> list[dict]:
    """Отсортировать расходы по сумме."""

    return sorted(expenses, key=lambda expense: expense["amount"])


def calculate_total(
    expenses: list[dict]
) -> float:
    """Рассчитать общую сумму расходов."""

    total = 0

    for expense in expenses:
        total += expense["amount"]

    return total


def calculate_average(
    expenses: list[dict]
) -> float:
    """Рассчитать среднюю сумму расхода."""

    if not expenses:
        return 0

    return calculate_total(expenses) / len(expenses)


def get_statistics(
    expenses: list[dict]
) -> dict:
    """Получить статистику расходов."""

    return {
        "count": len(expenses),
        "total": calculate_total(expenses),
        "average": calculate_average(expenses)
    }
