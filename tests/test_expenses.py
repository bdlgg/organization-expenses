
from models import Category, Department, Document, Expense
from models.expenses import (
    add_expense,
    calculate_average,
    calculate_total,
    find_expenses,
    filter_by_category,
    sort_expenses,
)


def create_test_expense(
    expense_id: int = 1,
    amount: float = 1500.0,
) -> Expense:
    category = Category("Продукты")
    department = Department("Бухгалтерия")
    document = Document("ДО-001")

    return Expense(
        expense_id,
        amount,
        category,
        department,
        document,
    )


def test_expense_creation():
    expense = create_test_expense()

    assert expense.id == 1
    assert expense.amount == 1500.0
    assert expense.category.name == "Продукты"
    assert expense.department.name == "Бухгалтерия"
    assert expense.document.number == "ДО-001"


def test_expense_object_interaction():
    category = Category("Продукты")
    department = Department("Бухгалтерия")
    document = Document("ДО-001")

    expense = Expense(
        1,
        1500.0,
        category,
        department,
        document,
    )

    assert expense.category is category
    assert expense.department is department
    assert expense.document is document


def test_expense_str():
    expense = create_test_expense()

    result = str(expense)

    assert "1500.00 руб." in result
    assert "Продукты" in result
    assert "Бухгалтерия" in result
    assert "ДО-001" in result


def test_expense_is_valid():
    valid_expense = create_test_expense(amount=1500.0)
    invalid_expense = create_test_expense(amount=-500.0)

    assert valid_expense.is_valid()
    assert not invalid_expense.is_valid()


def test_add_expense():
    expenses = []

    category = Category("Продукты")
    department = Department("Бухгалтерия")
    document = Document("ДО-001")

    add_expense(
        expenses,
        1,
        1500.0,
        category,
        department,
        document,
    )

    assert len(expenses) == 1
    assert expenses[0].id == 1
    assert expenses[0].amount == 1500.0
    assert expenses[0].category is category


def test_add_negative_expense():
    expenses = []

    category = Category("Продукты")
    department = Department("Бухгалтерия")
    document = Document("ДО-001")

    try:
        add_expense(
            expenses,
            1,
            -500.0,
            category,
            department,
            document,
        )
    except ValueError:
        pass
    else:
        assert False, "Отрицательный расход должен вызвать ValueError"

    assert len(expenses) == 0


def test_find_expenses():
    expense = create_test_expense()

    result = find_expenses([expense], "прод")

    assert len(result) == 1
    assert result[0] is expense


def test_find_expenses_by_department():
    expense = create_test_expense()

    result = find_expenses([expense], "бух")

    assert len(result) == 1
    assert result[0] is expense


def test_find_expenses_by_document():
    expense = create_test_expense()

    result = find_expenses([expense], "001")

    assert len(result) == 1
    assert result[0] is expense


def test_filter_by_category():
    products = Category("Продукты")
    transport = Category("Транспорт")

    department = Department("Бухгалтерия")
    document = Document("ДО-001")

    expenses = [
        Expense(1, 1000.0, products, department, document),
        Expense(2, 2000.0, transport, department, document),
        Expense(3, 3000.0, products, department, document),
    ]

    result = filter_by_category(expenses, products)

    assert len(result) == 2
    assert result[0].category is products
    assert result[1].category is products


def test_sort_expenses():
    category = Category("Продукты")
    department = Department("Бухгалтерия")
    document = Document("ДО-001")

    expenses = [
        Expense(1, 3000.0, category, department, document),
        Expense(2, 1000.0, category, department, document),
        Expense(3, 2000.0, category, department, document),
    ]

    result = sort_expenses(expenses)

    assert [expense.amount for expense in result] == [
        1000.0,
        2000.0,
        3000.0,
    ]


def test_calculate_total():
    category = Category("Продукты")
    department = Department("Бухгалтерия")
    document = Document("ДО-001")

    expenses = [
        Expense(1, 1000.0, category, department, document),
        Expense(2, 2000.0, category, department, document),
        Expense(3, 3000.0, category, department, document),
    ]

    assert calculate_total(expenses) == 6000.0


def test_calculate_average():
    category = Category("Продукты")
    department = Department("Бухгалтерия")
    document = Document("ДО-001")

    expenses = [
        Expense(1, 1000.0, category, department, document),
        Expense(2, 3000.0, category, department, document),
    ]

    assert calculate_average(expenses) == 2000.0


def test_calculate_average_empty():
    assert calculate_average([]) == 0.0
