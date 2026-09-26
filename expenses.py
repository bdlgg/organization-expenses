from typing import List

from categories import Category
from departments import Department
from documents import Document


class Expense:
    """Представляет расход организации."""

    def __init__(
        self,
        expense_id: int,
        amount: float,
        category: Category,
        department: Department,
        document: Document
    ):
        self.id = expense_id
        self.amount = amount
        self.category = category
        self.department = department
        self.document = document

    def is_valid(self) -> bool:
        """Проверить корректность расхода."""

        return (
            self.amount > 0
            and bool(self.category.name)
            and bool(self.department.name)
            and bool(self.document.number)
        )

    def get_info(self) -> str:
        """Получить информацию о расходе."""

        return (
            f"#{self.id} | "
            f"{self.amount:.2f} руб. | "
            f"{self.category.name} | "
            f"{self.department.name} | "
            f"{self.document.number}"
        )

    def to_dict(self) -> dict:
        """Преобразовать расход в словарь для JSON."""

        return {
            "id": self.id,
            "amount": self.amount,
            "category": self.category.name,
            "department": self.department.name,
            "document": self.document.number
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Expense":
        """Создать расход из словаря."""

        return cls(
            data["id"],
            data["amount"],
            Category(data["category"]),
            Department(data["department"]),
            Document(data["document"])
        )


def add_expense(
    expenses: List[Expense],
    amount: float,
    category: Category,
    department: Department,
    document: Document
) -> Expense:
    """Добавить новый расход в список."""

    expense_id = max(
        (expense.id for expense in expenses),
        default=0
    ) + 1

    expense = Expense(
        expense_id,
        amount,
        category,
        department,
        document
    )

    if not expense.is_valid():
        raise ValueError("Некорректные данные расхода.")

    expenses.append(expense)

    return expense


def find_expenses(
    expenses: List[Expense],
    query: str
) -> List[Expense]:
    """Найти расходы по категории, подразделению или документу."""

    result = []

    for expense in expenses:
        if (
            query.lower() in expense.category.name.lower()
            or query.lower() in expense.department.name.lower()
            or query.lower() in expense.document.number.lower()
        ):
            result.append(expense)

    return result


def filter_by_category(
    expenses: List[Expense],
    category: str
) -> List[Expense]:
    """Отобрать расходы по категории."""

    return [
        expense
        for expense in expenses
        if expense.category.name.lower() == category.lower()
    ]


def sort_expenses(
    expenses: List[Expense]
) -> List[Expense]:
    """Отсортировать расходы по сумме."""

    return sorted(
        expenses,
        key=lambda expense: expense.amount
    )


def calculate_total(
    expenses: List[Expense]
) -> float:
    """Рассчитать общую сумму расходов."""

    total = 0.0

    for expense in expenses:
        total += expense.amount

    return total


def calculate_average(
    expenses: List[Expense]
) -> float:
    """Рассчитать среднюю сумму расхода."""

    if not expenses:
        return 0.0

    return calculate_total(expenses) / len(expenses)


def get_statistics(
    expenses: List[Expense]
) -> dict:
    """Получить статистику расходов."""

    return {
        "count": len(expenses),
        "total": calculate_total(expenses),
        "average": calculate_average(expenses)
    }