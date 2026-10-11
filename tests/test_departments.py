from models.departments import (
    Department,
    add_department,
    find_department,
    sort_departments,
)


def test_department_creation():
    department = Department("Бухгалтерия")

    assert department.name == "Бухгалтерия"


def test_department_str():
    department = Department("Бухгалтерия")

    assert str(department) == "Бухгалтерия"


def test_department_matches():
    department = Department("Бухгалтерия")

    assert department.matches("бух")
    assert not department.matches("отдел продаж")


def test_add_department():
    departments = []

    add_department(departments, "Бухгалтерия")

    assert len(departments) == 1
    assert departments[0].name == "Бухгалтерия"


def test_find_department():
    departments = [
        Department("Бухгалтерия"),
        Department("Отдел продаж"),
    ]

    result = find_department(departments, "бух")

    assert len(result) == 1
    assert result[0].name == "Бухгалтерия"


def test_sort_departments():
    departments = [
        Department("Отдел продаж"),
        Department("Бухгалтерия"),
    ]

    result = sort_departments(departments)

    assert [department.name for department in result] == [
        "Бухгалтерия",
        "Отдел продаж",
    ]