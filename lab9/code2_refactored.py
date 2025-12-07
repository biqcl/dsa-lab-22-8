# Рефакторинг (разделение функции, промежуточные переменные)
def calculate_total(order):
    total = 0
    for item in order["items"]:
        total += item["price"] * item["quantity"]
    return total

def process_payment():
    print("Processing payment...")
    print("Payment successful")

def send_confirmation():
    print("Sending confirmation email...")
    print("Order complete.")

def process_order(order):
    total = calculate_total(order)
    print(f"Total: {total}")
    process_payment()
    send_confirmation()

# Пример теста
if __name__ == "__main__":
    order_example = {
        "items": [
            {"price": 100, "quantity": 2},
            {"price": 50, "quantity": 1}
        ]
    }
    process_order(order_example)