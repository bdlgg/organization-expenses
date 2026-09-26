from departments import (
    Department,
    add_department,
    find_department
)


def test_find_department():
    departments = []

    department = Department("IT")

    add_department(
        departments,
        department
    )

    result = find_department(
        departments,
        "it"
    )

    assert result is department