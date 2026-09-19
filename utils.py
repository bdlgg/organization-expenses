def input_float(prompt: str) -> float:
    """Запросить у пользователя положительное число."""

    while True:
        try:
            value = float(input(prompt))

            if value <= 0:
                print("Сумма должна быть больше нуля.")
                continue

            return value

        except ValueError:
            print("Введите число.")


def input_text(prompt: str) -> str:
    """Запросить непустой текст."""

    while True:
        value = input(prompt).strip()

        if value:
            return value

        print("Поле не может быть пустым.")


def input_int(prompt: str) -> int:
    """Запросить целое число."""

    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Введите целое число.")