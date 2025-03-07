import sys

# Считываем массив из параметров командной строки
if len(sys.argv) < 2:
    print("Ошибка: Необходимо передать массив чисел в качестве аргументов командной строки.")
    sys.exit(1)

array = list(map(int, sys.argv[1:]))

# Находим максимальный элемент и его индекс
max_value = max(array)
max_index = array.index(max_value) + 1
print(f"Максимальный элемент: {max_value}, его порядковый номер: {max_index}")

# Находим все нечетные числа и выводим их в порядке убывания
odd_numbers = [x for x in array if x % 2 != 0]
if odd_numbers:
    odd_numbers_sorted = sorted(odd_numbers, reverse=True)
    print("Нечетные числа в порядке убывания:", odd_numbers_sorted)
else:
    print("Нечетных чисел в массиве нет.")

