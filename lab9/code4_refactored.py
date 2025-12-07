# Рефакторинг (константы вместо магических чисел, комментарии)
TAX_THRESHOLD_LOW = 10000
TAX_THRESHOLD_MEDIUM = 20000
TAX_RATE_LOW = 0.10
TAX_RATE_MEDIUM = 0.15
TAX_RATE_HIGH = 0.20

def calculate_tax(income):
    # Прогрессивная налоговая система: 3 уровня дохода
    if income <= TAX_THRESHOLD_LOW:
        return income * TAX_RATE_LOW
    elif income <= TAX_THRESHOLD_MEDIUM:
        return income * TAX_RATE_MEDIUM
    else:
        return income * TAX_RATE_HIGH

# Пример теста
if __name__ == "__main__":
    print(calculate_tax(5000))   # 500
    print(calculate_tax(15000))  # 2250
    print(calculate_tax(30000))  # 6000