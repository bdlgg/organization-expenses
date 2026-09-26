import json
from typing import Callable, List, TypeVar


T = TypeVar("T")


def _load_data(
    filename: str,
    from_dict: Callable[[dict], T]
) -> List[T]:
    """Загрузить список объектов из JSON."""

    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)

        return [
            from_dict(item)
            for item in data
        ]

    except FileNotFoundError:
        return []

    except json.JSONDecodeError:
        return []


def _save_data(
    filename: str,
    items: List[T],
    to_dict: Callable[[T], dict]
) -> None:
    """Сохранить список объектов в JSON."""

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(
            [to_dict(item) for item in items],
            file,
            ensure_ascii=False,
            indent=4
        )


def load_expenses(filename: str) -> list:
    """Загрузить расходы."""

    from expenses import Expense

    return _load_data(
        filename,
        Expense.from_dict
    )


def save_expenses(
    filename: str,
    expenses: list
) -> None:
    """Сохранить расходы."""

    _save_data(
        filename,
        expenses,
        lambda expense: expense.to_dict()
    )


def load_categories(filename: str) -> list:
    """Загрузить категории."""

    from categories import Category

    return _load_data(
        filename,
        Category.from_dict
    )


def save_categories(
    filename: str,
    categories: list
) -> None:
    """Сохранить категории."""

    _save_data(
        filename,
        categories,
        lambda category: category.to_dict()
    )


def load_departments(filename: str) -> list:
    """Загрузить подразделения."""

    from departments import Department

    return _load_data(
        filename,
        Department.from_dict
    )


def save_departments(
    filename: str,
    departments: list
) -> None:
    """Сохранить подразделения."""

    _save_data(
        filename,
        departments,
        lambda department: department.to_dict()
    )


def load_documents(filename: str) -> list:
    """Загрузить документы."""

    from documents import Document

    return _load_data(
        filename,
        Document.from_dict
    )


def save_documents(
    filename: str,
    documents: list
) -> None:
    """Сохранить документы."""

    _save_data(
        filename,
        documents,
        lambda document: document.to_dict()
    )