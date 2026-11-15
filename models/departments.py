from typing import List


class Department:
    """Подразделение организации."""

    def __init__(self, name: str) -> None:
        self.name = name

    def matches(self, query: str) -> bool:
        """Проверить совпадение названия подразделения с запросом."""
        return query.lower() in self.name.lower()

    def __str__(self) -> str:
        """Вернуть строковое представление подразделения."""
        return self.name

    @classmethod
    def from_data(cls, data: dict) -> "Department":
        """Создать объект Department из данных JSON."""
        return cls(name=data["name"])


def add_department(
    departments: List[Department],
    name: str,
) -> None:
    """Добавить подразделение в коллекцию."""
    departments.append(Department(name))


def find_department(
    departments: List[Department],
    query: str,
) -> List[Department]:
    """Найти подразделения по названию."""
    return [
        department
        for department in departments
        if department.matches(query)
    ]


def filter_departments(
    departments: List[Department],
    query: str,
) -> List[Department]:
    """Отфильтровать подразделения по названию."""
    return find_department(departments, query)


def sort_departments(
    departments: List[Department],
) -> List[Department]:
    """Вернуть подразделения в алфавитном порядке."""
    return sorted(departments, key=lambda department: department.name)
