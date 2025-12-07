# Рефакторинг (словарь вместо множества аргументов)
def create_report(employee_data):
    # employee_data — словарь с данными сотрудника
    for key, value in employee_data.items():
        print(f"{key.capitalize()}: {value}")

# Пример теста
if __name__ == "__main__":
    employee = {
        "name": "Нина Демченко",
        "age": 21,
        "department": "НГТУ",
        "salary": 100000,
        "bonus": 5000,
        "performance_score": 85
    }
    create_report(employee)