from typing import List, Optional


class Department:
    """Представляет подразделение организации."""

    def __init__(self, name: str):
        self.name = name.strip()

    def matches(self, query: str) -> bool:
        """Проверить соответствие подразделения запросу."""

        return query.lower() in self.name.lower()

    def get_info(self) -> str:
        """Получить название подразделения."""

        return self.name

    def to_dict(self) -> dict:
        """Преобразовать подразделение в словарь."""

        return {
            "name": self.name
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Department":
        """Создать подразделение из словаря."""

        return cls(data["name"])


def add_department(
    departments: List[Department],
    department: Department
) -> None:
    """Добавить подразделение, если его еще нет."""

    if find_department(departments, department.name) is None:
        departments.append(department)


def find_department(
    departments: List[Department],
    name: str
) -> Optional[Department]:
    """Найти подразделение по названию."""

    for department in departments:
        if department.name.lower() == name.lower():
            return department

    return None


def filter_departments(
    departments: List[Department],
    query: str
) -> List[Department]:
    """Найти подразделения по подстроке."""

    return [
        department
        for department in departments
        if department.matches(query)
    ]


def sort_departments(
    departments: List[Department]
) -> List[Department]:
    """Отсортировать подразделения по названию."""

    return sorted(
        departments,
        key=lambda department: department.name.lower()
    )