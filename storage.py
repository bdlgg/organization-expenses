import json
from pathlib import Path
from typing import Any, Dict, List

from models import Category, Department, Document, Expense


def _load_data(file_path: str) -> List[Dict[str, Any]]:
    """Загрузить список данных из JSON-файла."""

    path = Path(file_path)

    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _save_data(
    file_path: str,
    data: List[Dict[str, Any]],
) -> None:
    """Сохранить список данных в JSON-файл."""

    path = Path(file_path)

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4,
        )


def load_categories(file_path: str) -> List[Category]:
    """Загрузить категории из JSON."""

    data = _load_data(file_path)

    return [
        Category.from_data(item)
        for item in data
    ]


def save_categories(
    file_path: str,
    categories: List[Category],
) -> None:
    """Сохранить категории в JSON."""

    data = [
        {
            "name": category.name,
        }
        for category in categories
    ]

    _save_data(file_path, data)


def load_departments(file_path: str) -> List[Department]:
    """Загрузить подразделения из JSON."""

    data = _load_data(file_path)

    return [
        Department.from_data(item)
        for item in data
    ]


def save_departments(
    file_path: str,
    departments: List[Department],
) -> None:
    """Сохранить подразделения в JSON."""

    data = [
        {
            "name": department.name,
        }
        for department in departments
    ]

    _save_data(file_path, data)


def load_documents(file_path: str) -> List[Document]:
    """Загрузить документы из JSON."""

    data = _load_data(file_path)

    return [
        Document.from_data(item)
        for item in data
    ]


def save_documents(
    file_path: str,
    documents: List[Document],
) -> None:
    """Сохранить документы в JSON."""

    data = [
        {
            "number": document.number,
        }
        for document in documents
    ]

    _save_data(file_path, data)


def load_expenses(
    file_path: str,
    categories: List[Category],
    departments: List[Department],
    documents: List[Document],
) -> List[Expense]:
    """Загрузить расходы из JSON и создать объекты Expense."""

    data = _load_data(file_path)

    return [
        Expense.from_data(
            item,
            categories,
            departments,
            documents,
        )
        for item in data
    ]


def save_expenses(
    file_path: str,
    expenses: List[Expense],
) -> None:
    """Сохранить расходы в JSON."""

    data = [
        {
            "id": expense.id,
            "amount": expense.amount,
            "category": expense.category.name,
            "department": expense.department.name,
            "document": expense.document.number,
        }
        for expense in expenses
    ]

    _save_data(file_path, data)