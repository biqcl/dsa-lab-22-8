# Считываем строку с клавиатуры
input_string = input("Введите строку: ")

# Заменяем все символы "a" на "о" на русском и английском языках
modified_string = input_string.replace('a', 'о').replace('а', 'о')

# Выводим количество замен как на русском, так и на английском
count_replacements = input_string.count('а') + input_string.count('a')
print(f"Количество замен: {count_replacements}")

# Подсчитываем и выводим количество всех символов в строке
total_characters = len(modified_string)
print(f"Количество всех символов в строке: {total_characters}")
print("Измененное слово: ", modified_string)

