# Рефакторинг (словарь вместо условий, плоская структура)
SHIPPING_RATES = {
    "USA": {"light": 10, "heavy": 20},
    "Canada": {"light": 15, "heavy": 25},
    "default": {"light": 30, "heavy": 50}
}

def calculate_shipping(country, weight):
    country_rates = SHIPPING_RATES.get(country, SHIPPING_RATES["default"])
    rate_key = "light" if weight < 5 else "heavy"
    return country_rates[rate_key]

# Пример теста
if __name__ == "__main__":
    print(calculate_shipping("USA", 3))   # 10
    print(calculate_shipping("Canada", 7)) # 25
    print(calculate_shipping("Germany", 4)) # 30