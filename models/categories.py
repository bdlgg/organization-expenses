from typing import List


class Category:
    """Категория расходов."""

    def __init__(self, name: str) -> None:
        self.name = name

    def matches(self, query: str) -> bool:
        """Проверить совпадение названия категории с запросом."""
        return query.lower() in self.name.lower()

    def __str__(self) -> str:
        """Вернуть строковое представление категории."""
        return self.name

    @classmethod
    def from_data(cls, data: dict) -> "Category":
        """Создать объект Category из данных JSON."""
        return cls(name=data["name"])


def add_category(categories: List[Category], name: str) -> None:
    """Добавить категорию в коллекцию."""
    categories.append(Category(name))


def find_category(
    categories: List[Category],
    query: str,
) -> List[Category]:
    """Найти категории по названию."""
    return [
        category
        for category in categories
        if category.matches(query)
    ]


def filter_categories(
    categories: List[Category],
    query: str,
) -> List[Category]:
    """Отфильтровать категории по названию."""
    return find_category(categories, query)


def sort_categories(
    categories: List[Category],
) -> List[Category]:
    """Вернуть категории в алфавитном порядке."""
    return sorted(categories, key=lambda category: category.name)
