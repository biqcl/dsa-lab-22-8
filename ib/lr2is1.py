import re
import os
from typing import List, Dict, Tuple, Set

# Улучшенные паттерны для обнаружения конфиденциальной информации
PATTERNS = {
    'personal_data': r'\b(пдн|персональн[а-я]*\s*данн[а-я]*|паспорт[а-я]*|фамили[а-я]*|им[ея]|отчеств[а-я]*|личн[а-я]*\s*данн[а-я]*)\b',
    'medical_info': r'\b(диагноз[а-я]*|болезн[ьи]|заболевани[а-я]*|медицинск[а-я]*\s*данн[а-я]*|врач[а-я]*|лечени[а-я]*|ветрянк[а-я]*|заразн[а-я]*)\b',
    'financial_info': r'\b(заработ[а-я]*|оборот[а-я]*|доход[а-я]*|зарплат[а-я]*|финанс[а-я]*|фнс|налог[а-я]*)\b',
    'commercial_secret': r'\b(коммерческ[а-я]*\s*тайн[а-я]*|формул[а-я]*|исследовани[а-я]*|ноу[-\s]*хау|секрет[а-я]*)\b',
    'bank_secret': r'\b(банковск[а-я]*\s*тайн[а-я]*|счет[а-я]*|вклад[а-я]*|кредитн[а-я]*\s*истори[а-я]*)\b',
    'tax_secret': r'\b(налогов[а-я]*\s*тайн[а-я]*|деклараци[а-я]*|отчетност[а-я]*)\b',
    'military_info': r'\b(пусков[а-я]*\s*установ[а-я]*|военн[а-я]*|секретн[а-я]*\s*объект[а-я]*|полигон[а-я]*|стрельб[а-я]*)\b',
    'coordinates': r'\b(\d+[.,]\d+\s*км|координат[а-я]*|местоположени[а-я]*|район[а-я]*)\b',
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'(\+7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}',
    'passport': r'\b[0-9]{4}\s?[№]?\s?[0-9]{6}\b',
    'credit_card': r'\b[0-9]{4}[\s\-]?[0-9]{4}[\s\-]?[0-9]{4}[\s\-]?[0-9]{4}\b',
    'inn': r'\b[0-9]{10,12}\b',
}

# Юридические основания для блокировки
LEGAL_BASES = {
    'personal_data': "Федеральный закон от 27.07.2006 N 152-ФЗ 'О персональных данных'",
    'medical_info': "Федеральный закон от 21.11.2011 N 323-ФЗ 'Об основах охраны здоровья граждан в Российской Федерации'",
    'financial_info': "Налоговый кодекс РФ, статья 102 'О налоговой тайне'",
    'commercial_secret': "Федеральный закон от 29.07.2004 N 98-ФЗ 'О коммерческой тайне'",
    'bank_secret': "Федеральный закон от 02.12.1990 N 395-1 'О банках и банковской деятельности' (банковская тайна)",
    'tax_secret': "Налоговый кодекс РФ, статья 102 'Налоговая тайна'",
    'military_info': "Федеральный закон 'О государственной тайне' и 'Об обороне'",
    'coordinates': "Федеральный закон 'О государственной тайне'",
    'default': "Федеральный закон от 27.07.2006 N 152-ФЗ 'О персональных данных'"
}

# Ключевые слова, указывающие на конфиденциальность
SENSITIVE_CONTEXT_WORDS = [
    'по секрету', 'конфиденциально', 'секретно', 'не разглашай', 'только между нами',
    'доверительно', 'строго между нами', 'никому не говори', 'это секрет',
    'не распространяй', 'секретная информация', 'закрытые данные'
]

# Проверяет наличие контекстных указаний на конфиденциальность
def contains_sensitive_context(text: str) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in SENSITIVE_CONTEXT_WORDS)

# Анализ текста на наличие конфиденциальной информации
def analyze_text(text: str) -> Dict[str, List[str]]:
    results = {}
    text_lower = text.lower()
    
    for data_type, pattern in PATTERNS.items():
        # Для текстовых паттернов используем поиск по нижнему регистру
        if data_type in ['email', 'phone', 'passport', 'credit_card', 'inn']:
            matches = re.findall(pattern, text, re.IGNORECASE)
        else:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
        
        if matches:
            # Для совпадений сохраняем оригинальный текст
            unique_matches = []
            for match in matches:
                if isinstance(match, tuple):  # Если паттерн содержит группы
                    match = next((m for m in match if m), '')
                if match and match not in unique_matches:
                    unique_matches.append(match)
            
            if unique_matches:
                results[data_type] = unique_matches
            
    # Проверяем контекстные указания на конфиденциальность
    if contains_sensitive_context(text_lower):
        if 'sensitive_context' not in results:
            results['sensitive_context'] = ['Обнаружены указания на конфиденциальный характер информации']
            
    return results

# Разделение текста на предложения
def split_into_sentences(text: str) -> List[str]:
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]

# Получение замены для типа конфиденциальных данных (теперь всегда звездочки)
def get_replacement(data_type: str, original_text: str = "") -> str:
    # Для конкретных типов данных используем звездочки вместо текстовых меток
    if data_type in ['email', 'phone', 'passport', 'credit_card', 'inn']:
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
    else:
        # Для текстовых данных используем простую замену на звездочки
        return '*****'

# Получение юридического основания для типа данных
def get_legal_base(data_types: Set[str]) -> str:
    for data_type in data_types:
        if data_type in LEGAL_BASES:
            return LEGAL_BASES[data_type]
    return LEGAL_BASES['default']

# Функция для замены на звездочки
def replace_with_stars(sentence: str, sensitive_data: Dict) -> str:
    processed_sentence = sentence
    
    print(f"\nТекущее предложение: {sentence}")
    
    # Собираем все совпадения для этого предложения
    all_matches = []
    for data_type, matches in sensitive_data.items():
        for match in matches:
            if match.lower() in processed_sentence.lower():
                all_matches.append((data_type, match))
    
    if not all_matches:
        return processed_sentence
    
    print("Найденные конфиденциальные данные для замены:")
    for i, (data_type, match) in enumerate(all_matches, 1):
        print(f"{i}. {data_type}: '{match}'")
    
    # Заменяем все найденные данные на звездочки
    for data_type, match in all_matches:
        replacement = get_replacement(data_type, match)
        # Используем регулярное выражение для точной замены с учетом регистра
        processed_sentence = re.sub(re.escape(match), replacement, processed_sentence, flags=re.IGNORECASE)
        print(f"Заменено '{match}' на '{replacement}'")
    
    print(f"Результат: {processed_sentence}")
    return processed_sentence

# Обработка предложения в соответствии с выбранным действием
def process_sentence(sentence: str, sensitive_data: Dict, action: str) -> Tuple[str, bool]:
    if action == 'a':  # Удалить
        return "", False
    elif action == 'b':  # Заменить на звездочки
        processed_sentence = replace_with_stars(sentence, sensitive_data)
        return processed_sentence, False
    else:  # Ничего не делать
        return sentence, True  # Флаг блокировки

# Обработка всего текста
def process_text(text: str, sensitive_data: Dict) -> Tuple[str, bool]:
    sentences = split_into_sentences(text)
    processed_sentences = []
    is_blocked = False
    found_violation_types = set()
    
    for i, sentence in enumerate(sentences):
        # Проверяем, содержит ли предложение конфиденциальные данные
        sentence_sensitive_data = {}
        sentence_has_sensitive_data = False
        
        for data_type, matches in sensitive_data.items():
            sentence_matches = []
            for match in matches:
                if match.lower() in sentence.lower():
                    sentence_matches.append(match)
            
            if sentence_matches:
                sentence_sensitive_data[data_type] = sentence_matches
                sentence_has_sensitive_data = True
                found_violation_types.add(data_type)
        
        if not sentence_has_sensitive_data:
            processed_sentences.append(sentence)
            continue
            
        # Предложение содержит конфиденциальные данные
        print("\n" + "="*80)
        print(f"Предложение {i+1}/{len(sentences)}: Обнаружена конфиденциальная информация:")
        print(f"Текст: {sentence}")
        
        # Показываем какие типы данных найдены
        found_types = list(sentence_sensitive_data.keys())
        print(f"Типы конфиденциальной информации: {', '.join(found_types)}")
        
        # Показываем конкретные найденные данные
        print("Найденные конфиденциальные данные:")
        for data_type, matches in sentence_sensitive_data.items():
            for j, match in enumerate(matches):
                print(f"  - {data_type}: '{match}'")
        
        # Запрашиваем действие у пользователя
        while True:
            print("\nВыберите действие для этого предложения:")
            print("a - Удалить предложение")
            print("b - Заменить конфиденциальные данные на *****")
            print("c - Ничего не делать (файл будет заблокирован)")
            action = input("Ваш выбор (a/b/c): ").lower()
            
            if action in ['a', 'b', 'c']:
                break
            print("Неверный выбор! Попробуйте снова.")
        
        # Обрабатываем предложение
        processed_sentence, should_block = process_sentence(sentence, sentence_sensitive_data, action)
        
        if action == 'a':  # Удаление - не добавляем предложение
            print("✓ Предложение удалено")
            continue
        elif action == 'b':  # Замена на звездочки
            print("✓ Конфиденциальные данные заменены на *****")
            processed_sentences.append(processed_sentence)
        else:  # Ничего не делать
            print("⚠ Предложение оставлено без изменений")
            processed_sentences.append(processed_sentence)
            is_blocked = is_blocked or should_block
        
        print("="*80)
    
    # Собираем обработанный текст
    result_text = '. '.join(processed_sentences)
    if processed_sentences and not result_text.endswith('.'):
        result_text += '.'
        
    return result_text, is_blocked, found_violation_types

def analyze_keyboard_input():
    
    print("АНАЛИЗ ТЕКСТА С КЛАВИАТУРЫ")
    
    text = input("Введите текст для анализа:\n")
    
    if not text.strip():
        print("Ошибка: Введен пустой текст!")
        return False
        
    return analyze_and_process(text, "введенный текст")

# Анализ текста в файле
def analyze_file_input():
    
    print("АНАЛИЗ ФАЙЛА")
    
    file_path = input("Введите путь к файлу: ")
    
    if not os.path.exists(file_path):
        print(f"Ошибка: Файл '{file_path}' не найден!")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            
        if not text.strip():
            print("Ошибка: Файл пустой!")
            return False
            
        print(f"Файл '{file_path}' успешно загружен")
        return analyze_and_process(text, f"файл '{file_path}'", file_path)
        
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return False

# Основная функция анализа и обработки
def analyze_and_process(text: str, source_name: str, file_path: str = None) -> bool:
    # Шаг 1: Анализ текста
    print("\nПроводим анализ текста...")
    sensitive_data = analyze_text(text)
    
    if not sensitive_data:
        print(f"\n✓ {source_name.upper()} БЕЗОПАСЕН")
        print("Конфиденциальная информация отсутствует.")
        return True
    
    # Шаг 2: Показываем найденную информацию
    print("\n" + "!"*60)
    print("ПРЕДУПРЕЖДЕНИЕ: Обнаружена конфиденциальная информация!")
    print("!"*60)
    print("\nНайденные типы конфиденциальных данных:")
    total_matches = 0
    for data_type, matches in sensitive_data.items():
        print(f"\n{data_type.upper()}: {len(matches)} совпадений")
        for j, match in enumerate(matches[:5]):  # Показываем первые 5 совпадений
            print(f"  {j+1}. '{match}'")
        if len(matches) > 5:
            print(f"  ... и еще {len(matches) - 5} совпадений")
        total_matches += len(matches)
    
    print(f"\nВсего найдено конфиденциальных данных: {total_matches}")
    
    # Шаг 3: Обработка текста
   
    print("\nПриступаем к обработке текста...")
    
    processed_text, is_blocked, violation_types = process_text(text, sensitive_data)
    
    # Шаг 4: Итоговый результат
    print("\n" + "="*80)
    print("ИТОГОВЫЙ РЕЗУЛЬТАТ АНАЛИЗА")
    print("="*80)
    
    if is_blocked:
        legal_base = get_legal_base(violation_types)
        print(f"\n❌ {source_name.upper()} ЗАБЛОКИРОВАН")
        print(f"Основание: {legal_base}")
        print("Причина: Обнаружена необработанная конфиденциальная информация!")
        result = False
    else:
        print(f"\n✅ {source_name.upper()} БЕЗОПАСЕН")
        print("Конфиденциальная информация отсутствует или успешно обработана!")
        result = True
        
        # Предлагаем сохранить обработанный текст (для файлов)
        if file_path and input("\nСохранить обработанный текст в файл? (y/n): ").lower() == 'y':
            try:
                base_name = os.path.basename(file_path)
                name, ext = os.path.splitext(base_name)
                new_path = f"safe_{name}{ext}"
                
                with open(new_path, 'w', encoding='utf-8') as f:
                    f.write(processed_text)
                print(f"✓ Обработанный текст сохранен в: {new_path}")

                # Показываем preview обработанного текста
                if input("Показать обработанный текст? (y/n): ").lower() == 'y':
                    print("\nОБРАБОТАННЫЙ ТЕКСТ:")
                    print("-" * 50)
                    print(processed_text[:500] + "..." if len(processed_text) > 500 else processed_text)
                    print("-" * 50)
                    
            except Exception as e:
                print(f"❌ Ошибка при сохранении файла: {e}")
    
    return result

def main():
    while True:
        
        print("\n" + "="*60)
        print("АНАЛИЗАТОР КОНФИДЕНЦИАЛЬНОЙ ИНФОРМАЦИИ")
        print("="*60)
        print("1. Анализ текста с клавиатуры")
        print("2. Анализ текста из файла")
        print("3. Выход")
        
        choice = input("\nВыберите опцию (1-3): ").strip()
        
        if choice == '1':
            analyze_keyboard_input()
        elif choice == '2':
            analyze_file_input()
        elif choice == '3':
            print("\nДо свидания! Программа завершена.")
            break
        else:
            print("Неверный выбор! Попробуйте снова.")
        
        input("\nНажмите Enter для продолжения...")

# Запуск программы
if __name__ == "__main__":
    main()
    