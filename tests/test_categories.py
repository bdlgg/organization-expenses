from models.categories import (
    Category,
    add_category,
    find_category,
    sort_categories,
)


def test_category_creation():
    category = Category("Продукты")

    assert category.name == "Продукты"


def test_category_str():
    category = Category("Продукты")

    assert str(category) == "Продукты"


def test_category_matches():
    category = Category("Продукты")

    assert category.matches("прод")
    assert not category.matches("транспорт")


def test_add_category():
    categories = []

    add_category(categories, "Продукты")

    assert len(categories) == 1
    assert categories[0].name == "Продукты"


def test_find_category():
    categories = [
        Category("Продукты"),
        Category("Транспорт"),
    ]

    result = find_category(categories, "прод")

    assert len(result) == 1
    assert result[0].name == "Продукты"


def test_sort_categories():
    categories = [
        Category("Транспорт"),
        Category("Продукты"),
    ]

    result = sort_categories(categories)

    assert [category.name for category in result] == [
        "Продукты",
        "Транспорт",
    ]
