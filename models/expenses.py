from typing import Dict, List

from .categories import Category
from .departments import Department
from .documents import Document


class Expense:
    """Расход организации."""

    def __init__(
        self,
        expense_id: int,
        amount: float,
        category: Category,
        department: Department,
        document: Document,
    ) -> None:
        self.id = expense_id
        self.amount = amount
        self.category = category
        self.department = department
        self.document = document

    def is_valid(self) -> bool:
        """Проверить корректность суммы расхода."""
        return self.amount >= 0

    def __str__(self) -> str:
        """Вернуть строковое представление расхода."""
        return (
            f"{self.id}: {self.amount:.2f} руб. | "
            f"{self.category} | "
            f"{self.department} | "
            f"документ {self.document}"
        )

    @classmethod
    def from_data(
        cls,
        data: dict,
        categories: List[Category],
        departments: List[Department],
        documents: List[Document],
    ) -> "Expense":
        """Создать объект Expense из данных JSON."""

        category = next(
            category
            for category in categories
            if category.name == data["category"]
        )

        department = next(
            department
            for department in departments
            if department.name == data["department"]
        )

        document = next(
            document
            for document in documents
            if document.number == data["document"]
        )

        return cls(
            expense_id=data["id"],
            amount=data["amount"],
            category=category,
            department=department,
            document=document,
        )


def add_expense(
    expenses: List[Expense],
    expense_id: int,
    amount: float,
    category: Category,
    department: Department,
    document: Document,
) -> None:
    """Создать расход и добавить его в коллекцию."""

    expense = Expense(
        expense_id=expense_id,
        amount=amount,
        category=category,
        department=department,
        document=document,
    )

    if not expense.is_valid():
        raise ValueError("Сумма расхода не может быть отрицательной.")

    expenses.append(expense)


def find_expenses(
    expenses: List[Expense],
    query: str,
) -> List[Expense]:
    """Найти расходы по категории, подразделению или документу."""

    query = query.lower()

    return [
        expense
        for expense in expenses
        if (
            query in expense.category.name.lower()
            or query in expense.department.name.lower()
            or query in expense.document.number.lower()
        )
    ]


def filter_by_category(
    expenses: List[Expense],
    category: Category,
) -> List[Expense]:
    """Отфильтровать расходы по категории."""

    return [
        expense
        for expense in expenses
        if expense.category.name == category.name
    ]


def sort_expenses(
    expenses: List[Expense],
) -> List[Expense]:
    """Отсортировать расходы по сумме."""

    return sorted(expenses, key=lambda expense: expense.amount)


def calculate_total(expenses: List[Expense]) -> float:
    """Рассчитать общую сумму расходов."""
    return sum(expense.amount for expense in expenses)


def calculate_average(expenses: List[Expense]) -> float:
    """Рассчитать среднюю сумму расхода."""

    if not expenses:
        return 0.0

    return calculate_total(expenses) / len(expenses)


def get_statistics(expenses: List[Expense]) -> Dict[str, float]:
    """Получить основные статистические показатели."""

    return {
        "total": calculate_total(expenses),
        "average": calculate_average(expenses),
        "count": float(len(expenses)),
    }