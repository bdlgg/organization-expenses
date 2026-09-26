from typing import List, Optional


class Category:
    """Представляет категорию расхода."""

    def __init__(self, name: str):
        self.name = name.strip()

    def matches(self, query: str) -> bool:
        """Проверить соответствие категории поисковому запросу."""

        return query.lower() in self.name.lower()

    def get_info(self) -> str:
        """Получить название категории."""

        return self.name

    def to_dict(self) -> dict:
        """Преобразовать категорию в словарь."""

        return {
            "name": self.name
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Category":
        """Создать категорию из словаря."""

        return cls(data["name"])


def add_category(
    categories: List[Category],
    category: Category
) -> None:
    """Добавить категорию, если ее еще нет."""

    if find_category(categories, category.name) is None:
        categories.append(category)


def find_category(
    categories: List[Category],
    name: str
) -> Optional[Category]:
    """Найти категорию по названию."""

    for category in categories:
        if category.name.lower() == name.lower():
            return category

    return None


def filter_categories(
    categories: List[Category],
    query: str
) -> List[Category]:
    """Найти категории по подстроке."""

    return [
        category
        for category in categories
        if category.matches(query)
    ]


def sort_categories(
    categories: List[Category]
) -> List[Category]:
    """Отсортировать категории по названию."""

    return sorted(
        categories,
        key=lambda category: category.name.lower()
    )