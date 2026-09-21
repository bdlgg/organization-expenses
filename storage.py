import json


def load_expenses(filename: str) -> list[dict]:
    """Загрузить расходы из JSON-файла."""

    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def save_expenses(
    filename: str,
    expenses: list[dict]
) -> None:
    """Сохранить расходы в JSON-файл."""

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(
            expenses,
            file,
            ensure_ascii=False,
            indent=4
        )
