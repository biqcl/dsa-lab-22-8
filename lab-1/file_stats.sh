#!/bin/bash

# Проверяем, передан ли аргумент
if [ $# -eq 0 ]; then
    echo "Ошибка: Не указан файл" >&2
    echo "Использование: $0 <текстовый_файл>" >&2
    exit 1
fi

filename="$1"

# Проверяем, существует ли файл
if [ ! -f "$filename" ]; then
    echo "Ошибка: Файл '$filename' не существует" >&2
    exit 1
fi

# Проверяем, является ли файл текстовым 
if [ ! -r "$filename" ]; then
    echo "Ошибка: Файл '$filename' недоступен для чтения" >&2
    exit 1
fi

# Вычисляем статистику
line_count=$(grep -c '^' "$filename")
word_count=$(wc -w < "$filename")
char_count=$(wc -m < "$filename")

# Выводим статистику
echo "Статистика для файла: $filename"
echo "Количество строк: $line_count"
echo "Количество слов: $word_count"
echo "Количество символов: $char_count"
