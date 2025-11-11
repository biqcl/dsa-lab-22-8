import re
import os
from typing import Dict, List, Tuple
from pathlib import Path

# Паттерны для обнаружения ПДн
PATTERNS = {
    'phone': r'[\+7|8][\s\(\-\d\)]{10,15}', 
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'passport': r'\b\d{4}\s?[№#]?\s?\d{6}\b',
    'snils': r'\b\d{3}[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{2}\b',
    'inn': r'\b\d{10,12}\b',
    'card_number': r'\b(?:\d{4}[\s\-]?){3}\d{4}\b',
    'name': r'\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?\b',
    'address': r'(?:ул\.|улица|пр\.|проспект|пер\.|переулок)\s+[А-Яа-яёЁ\-]+\s*,\s*(?:д\.|дом)\s*\d+\s*(?:,\s*(?:кв\.|квартира)\s*\d+)?'
}

# Получение замены для типа конфиденциальных данных (теперь всегда звездочки)
def get_replacement(data_type: str, original_text: str = "") -> str:
    # Для конкретных типов данных используем звездочки вместо текстовых меток
    if data_type in ['email', 'passport', 'snils', 'inn']:
        # Для структурированных данных заменяем на соответствующее количество звездочек
        if original_text:
            # Сохраняем первую и последнюю буквы/цифры для лучшей читаемости
            if len(original_text) <= 3:
                return '***'
            elif len(original_text) <= 6:
                return original_text[0] + '***' + original_text[-1]
            else:
                return original_text[0] + '*****' + original_text[-1]
        return '*****'
    elif data_type == 'phone':
        # Для телефонов сохраняем начало номера (+7 или 8) и последнюю цифру
        if original_text:
            # Оставляем только цифры для анализа
            digits_only = re.sub(r'\D', '', original_text)
            
            # Определяем начало номера
            if original_text.startswith('+7'):
                prefix = '+7'
            elif original_text.startswith('8'):
                prefix = '8'
            elif digits_only.startswith('7'):
                prefix = '+7'
            else:
                prefix = original_text[0] if original_text else ''
            
            # Сохраняем последнюю цифру
            last_digit = original_text[-1] if original_text else ''
            
            # Создаем замену с сохранением префикса
            if len(original_text) <= 5:
                return prefix + '***'
            else:
                return prefix + '*****' + last_digit
        return '*****'
    elif data_type == 'card_number':
        # Для номеров карт сохраняем первые 4 и последние 4 цифры
        if original_text:
            # Убираем все нецифровые символы
            digits_only = re.sub(r'\D', '', original_text)
            if len(digits_only) == 16:
                return digits_only[:4] + '********' + digits_only[-4:]
            else:
                # Для других форматов используем обычную замену
                return original_text[0] + '*****' + original_text[-1]
        return '*****'
    elif data_type == 'name':
        # Для ФИО заменяем только фамилию (последнее слово) на первую букву с точкой
        if original_text:
            words = original_text.split()
            if len(words) >= 2:
                # Заменяем фамилию (последнее слово) на первую букву с точкой
                surname = words[-1]
                # Оставляем имя и отчество (первые слова) без изменений
                other_names = words[:-1]
                return " ".join(other_names) + f" {surname[0]}."
            else:
                # Если только одно слово, возвращаем как есть
                return original_text
        return original_text
    elif data_type == 'address':
        # Для адреса заменяем на звездочки, сохраняя структуру
        if original_text:
            # Разбиваем адрес на части и заменяем каждую часть
            parts = re.split(r'([,\s]+)', original_text)
            anonymized_parts = []
            for part in parts:
                if part.strip() and not re.match(r'^[,\s]+$', part):
                    if part.isdigit():
                        # Для цифр заменяем на звездочки
                        if len(part) <= 3:
                            anonymized_parts.append('***')
                        else:
                            anonymized_parts.append(part[0] + '***' + part[-1])
                    elif re.match(r'^(ул\.|улица|пр\.|проспект|пер\.|переулок|д\.|дом|кв\.|квартира)$', part):
                        # Для служебных слов оставляем как есть или заменяем на короткие звездочки
                        anonymized_parts.append('***')
                    else:
                        # Для названий улиц и других слов
                        if len(part) <= 3:
                            anonymized_parts.append('***')
                        elif len(part) <= 6:
                            anonymized_parts.append(part[0] + '***' + part[-1])
                        else:
                            anonymized_parts.append(part[0] + '*****' + part[-1])
                else:
                    # Сохраняем разделители (запятые, пробелы)
                    anonymized_parts.append(part)
            return ''.join(anonymized_parts)
        return '*****'
    else:
        # Для неизвестных типов данных используем простую замену на звездочки
        return '*****'

# Обнаружение ПДн в тексте
def detect_pdn(text: str) -> Dict[str, List[str]]:
    """Обнаружение персональных данных в тексте"""
    detected = {}
    
    for pdn_type, pattern in PATTERNS.items():
        if pdn_type in ['email', 'phone', 'passport', 'card_number', 'inn']:
            # Для этих типов ищем без учета регистра
            matches = re.findall(pattern, text, re.IGNORECASE)
        else:
            matches = re.findall(pattern, text)
        
        if matches:
            clean_matches = []
            for match in matches:
                if isinstance(match, tuple):
                    # Берем первую непустую группу из кортежа
                    match = next((m for m in match if m), '')
                
                # Для телефонов проверяем, что это действительно номер
                if pdn_type == 'phone':
                    # Оставляем только цифры и проверяем длину
                    digits_only = re.sub(r'\D', '', match)
                    if len(digits_only) < 10:  # Слишком короткий для телефона
                        continue
                
                # Для адреса очищаем от лишних пробелов
                if pdn_type == 'address':
                    match = re.sub(r'\s+', ' ', match).strip()
                
                if match and match not in clean_matches:
                    clean_matches.append(match)
            
            if clean_matches:
                detected[pdn_type] = clean_matches
    
    # Дополнительный поиск телефонов в сложных форматах
    complex_phones = find_complex_phones(text)
    if complex_phones:
        if 'phone' not in detected:
            detected['phone'] = []
        detected['phone'].extend(complex_phones)
        detected['phone'] = list(set(detected['phone']))  # Убираем дубликаты
    
    # Дополнительный поиск номеров карт в разных форматах
    complex_cards = find_complex_cards(text)
    if complex_cards:
        if 'card_number' not in detected:
            detected['card_number'] = []
        detected['card_number'].extend(complex_cards)
        detected['card_number'] = list(set(detected['card_number']))
    
    return detected

# Поиск телефонов в сложных форматах
def find_complex_phones(text: str) -> List[str]:
    """Поиск телефонов в различных форматах"""
    phone_patterns = [
        # Формат: +7 (912) 345-67-89
        r'\+\d\s*\(\d{3}\)\s*\d{3}[\s\-]?\d{2}[\s\-]?\d{2}',
        # Формат: 8 (912) 345-67-89  
        r'8\s*\(\d{3}\)\s*\d{3}[\s\-]?\d{2}[\s\-]?\d{2}',
        # Формат: +79123456789
        r'\+\d{11}',
        # Формат: 89123456789
        r'8\d{10}',
        # Формат: +7-912-345-67-89
        r'\+\d[\-\d]{10,15}',
        # Формат: 8-912-345-67-89
        r'8[\-\d]{10,15}',
    ]
    
    phones = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # Проверяем, что это действительно телефон (достаточно цифр)
            digits = re.sub(r'\D', '', match)
            if len(digits) >= 10:  # Минимальная длина для телефона
                phones.append(match)
    
    return list(set(phones))

# Поиск номеров карт в разных форматах
def find_complex_cards(text: str) -> List[str]:
    """Поиск номеров банковских карт в различных форматах"""
    card_patterns = [
        # Формат: 1234 5678 9012 3456
        r'\b\d{4}\s\d{4}\s\d{4}\s\d{4}\b',
        # Формат: 1234-5678-9012-3456
        r'\b\d{4}\-\d{4}\-\d{4}\-\d{4}\b',
        # Формат: 1234567890123456
        r'\b\d{16}\b',
    ]
    
    cards = []
    for pattern in card_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # Проверяем, что это действительно номер карты (16 цифр)
            digits = re.sub(r'\D', '', match)
            if len(digits) == 16:
                cards.append(match)
    
    return list(set(cards))

# Улучшенная функция для замены с учетом границ слов
def replace_pdn_in_text(text: str, pdn_type: str, matches: List[str], action: str) -> str:
    """Замена ПДн в тексте с учетом границ слов"""
    processed_text = text
    
    for match in matches:
        if action == 'delete':
            replacement = '[УДАЛЕНО]'
        elif action == 'anonymize':
            replacement = get_replacement(pdn_type, match)
        
        if pdn_type in ['address', 'phone', 'card_number']:
            # Для адресов, телефонов и карт используем точное совпадение
            pattern = re.escape(match)
            processed_text = re.sub(pattern, replacement, processed_text)
        else:
            # Для остальных типов используем границы слов
            pattern = r'\b' + re.escape(match) + r'\b'
            processed_text = re.sub(pattern, replacement, processed_text)
    
    return processed_text

# Обезличивание текста
def anonymize_text(text: str, action: str = 'anonymize') -> Tuple[str, Dict[str, List[str]]]:
    """Обезличивание текста с выбранным действием"""
    detected_pdn = detect_pdn(text)
    processed_text = text
    
    print("\nОбнаруженные ПДн:")
    for pdn_type, matches in detected_pdn.items():
        print(f"  {pdn_type}: {matches}")
    
    if not detected_pdn:
        print("ПДн не обнаружены!")
        return text, detected_pdn
    
    # Обрабатываем каждый тип ПДн
    for pdn_type, matches in detected_pdn.items():
        processed_text = replace_pdn_in_text(processed_text, pdn_type, matches, action)
        
        # Выводим информацию о заменах
        for match in matches:
            if action == 'delete':
                print(f"Удалено: '{match}'")
            elif action == 'anonymize':
                replacement = get_replacement(pdn_type, match)
                print(f"Заменено: '{match}' -> '{replacement}'")
    
    return processed_text, detected_pdn

# Обработка файла
def process_file(filename: str, action: str = 'anonymize') -> Tuple[str, Dict[str, List[str]]]:
    """Обработка файла с ПДн"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
        
        print(f"\nЗагружен файл: {filename}")
        print(f"Размер файла: {len(content)} символов")
        
        processed_content, detected_pdn = anonymize_text(content, action)
        
        # Извлекаем только имя файла из полного пути
        file_path = Path(filename)
        file_name = file_path.name
        
        # Сохранение обработанного файла
        if action == 'delete':
            output_filename = f"deleted_{file_name}"
        else:
            output_filename = f"anonymized_{file_name}"
        
        with open(output_filename, 'w', encoding='utf-8') as file:
            file.write(processed_content)
        
        print(f"\nОбработанный файл сохранен как: {output_filename}")
        return processed_content, detected_pdn
        
    except FileNotFoundError:
        print(f"Ошибка: Файл '{filename}' не найден!")
        return "", {}
    except Exception as e:
        print(f"Ошибка при обработке файла: {e}")
        return "", {}

# Ввод текста с клавиатуры
def input_from_keyboard() -> str:
    """Ввод текста с клавиатуры"""
    print("\nВведите текст (для завершения ввода введите пустую строку):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    
    text = "\n".join(lines)
    
    if not text.strip():
        print("Ошибка: Введен пустой текст!")
        return ""
    
    print(f"\nВведено текста: {len(text)} символов")
    return text

# Выбор действия для обработки
def select_action() -> str:
    """Выбор действия для обработки ПДн"""
    print("\nВыберите действие для обработки ПДн:")
    print("1 - Удалить ПДн")
    print("2 - Обезличить ПДн (заменить на звездочки)")
    print("3 - Отмена")
    
    while True:
        choice = input("Ваш выбор (1-3): ").strip()
        
        if choice == '1':
            return 'delete'
        elif choice == '2':
            return 'anonymize'
        elif choice == '3':
            return 'cancel'
        else:
            print("Неверный выбор! Попробуйте снова.")

# Показать статистику обработки
def show_statistics(detected_pdn: Dict[str, List[str]], original_text: str, processed_text: str):
    """Показать статистику обработки"""
    total_detected = sum(len(matches) for matches in detected_pdn.values())
    
    print("\n" + "="*50)
    print("СТАТИСТИКА ОБРАБОТКИ")
    print("="*50)
    print(f"Обнаружено типов ПДн: {len(detected_pdn)}")
    print(f"Всего совпадений ПДн: {total_detected}")
    print(f"Исходный размер: {len(original_text)} символов")
    print(f"Обработанный размер: {len(processed_text)} символов")
    
    if detected_pdn:
        print("\nДетали обнаруженных ПДн:")
        for pdn_type, matches in detected_pdn.items():
            print(f"  {pdn_type}: {len(matches)} совпадений")
    
    print("="*50)

# Основная функция
def main():
    """Основная функция программы"""
    while True:
        print("\n" + "="*50)
        print("ОБЕЗЛИЧИВАТЕЛЬ ПЕРСОНАЛЬНЫХ ДАННЫХ (ПДн)")
        print("="*50)
        print("1. Ввод текста с клавиатуры")
        print("2. Загрузка из файла")
        print("3. Выход")
        
        choice = input("\nВыберите опцию (1-3): ").strip()
        
        if choice == '1':
            # Ввод с клавиатуры
            text = input_from_keyboard()
            if not text:
                continue
                
            action = select_action()
            if action == 'cancel':
                continue
                
            processed_text, detected_pdn = anonymize_text(text, action)
            
            print("\n" + "="*50)
            print("РЕЗУЛЬТАТ ОБРАБОТКИ:")
            print("="*50)
            print(processed_text)
            print("="*50)
            
            show_statistics(detected_pdn, text, processed_text)
            
            # Предложение сохранить в файл
            if input("\nСохранить результат в файл? (y/n): ").lower() == 'y':
                filename = input("Введите имя файла: ").strip()
                if filename:
                    try:
                        with open(filename, 'w', encoding='utf-8') as file:
                            file.write(processed_text)
                        print(f"Результат сохранен в файл: {filename}")
                    except Exception as e:
                        print(f"Ошибка при сохранении файла: {e}")
        
        elif choice == '2':
            # Загрузка из файла
            filename = input("Введите путь к файлу: ").strip()
            if not filename:
                print("Ошибка: Не указано имя файла!")
                continue
                
            if not os.path.exists(filename):
                print(f"Ошибка: Файл '{filename}' не найден!")
                continue
                
            action = select_action()
            if action == 'cancel':
                continue
                
            processed_text, detected_pdn = process_file(filename, action)
            
            if processed_text:
                show_statistics(detected_pdn, "содержимое файла", processed_text)
                
                # Показ preview обработанного текста
                if input("\nПоказать обработанный текст? (y/n): ").lower() == 'y':
                    print("\n" + "="*50)
                    print("ПРЕВЬЮ ОБРАБОТАННОГО ТЕКСТА:")
                    print("="*50)
                    preview = processed_text[:500] + "..." if len(processed_text) > 500 else processed_text
                    print(preview)
                    print("="*50)
        
        elif choice == '3':
            print("\nПрограмма завершена. До свидания!")
            break
        
        else:
            print("Неверный выбор! Попробуйте снова.")
        
        input("\nНажмите Enter для продолжения...")

# Запуск программы
if __name__ == "__main__":
    main()

