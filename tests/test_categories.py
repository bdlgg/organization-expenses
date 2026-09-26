from categories import (
    Category,
    add_category,
    find_category
)


def test_find_category():
    categories = []

    category = Category("Оборудование")

    add_category(
        categories,
        category
    )

    result = find_category(
        categories,
        "оборудование"
    )

    assert result is category