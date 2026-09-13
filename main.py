def check_amount(amount):
    return amount > 0


def get_category(category):
    return category


def calculate_total(amount, tax):
    return amount + amount * tax / 100


amount = float(input("Введите сумму расхода: "))
category = input("Введите категорию: ")

print("Сумма корректна:", check_amount(amount))
print("Категория:", get_category(category))
print("Итоговая сумма:", calculate_total(amount, 20))