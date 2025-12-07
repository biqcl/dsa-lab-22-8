import asyncio
import json
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any
import sys


class TransactionProcessor:
    def __init__(self, warning_threshold: float = 5000):
        self.warning_threshold = warning_threshold
        self.category_totals = defaultdict(float)  # Суммы по категориям
        self.category_transactions = defaultdict(list)  # Транзакции по категориям
    
    # Асинхронное чтение файла
    async def read_transactions_stream(self, filename: str):
        print(f"Чтение транзакций из файла: {filename}")
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                transactions = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Ошибка при чтении файла: {e}")
            return
        
        # Имитация асинхронного чтения
        for transaction in transactions:
            await asyncio.sleep(0.001)
            yield transaction
    
    # Обработка одной транзакции
    async def process_transaction(self, transaction: Dict[str, Any]):
        category = transaction["category"]
        amount = transaction["amount"]
        
        self.category_transactions[category].append(transaction)
        self.category_totals[category] += amount
        
        # Проверка превышения порога
        await self.check_threshold(category, self.category_totals[category])
        
        return category, amount
    
    # Проверка порога расходов
    async def check_threshold(self, category: str, total: float):
        if total > self.warning_threshold:
            print(f"  ВНИМАНИЕ: Расходы в категории '{category}' "
                  f"превысили {self.warning_threshold:.2f}. "
                  f"Текущая сумма: {total:.2f}")
    
    # Обработка всего потока
    async def process_stream(self, filename: str):
        print(f"Начало обработки транзакций")
        print("-" * 50)
        
        transaction_count = 0
        stream = self.read_transactions_stream(filename)
        
        async for transaction in stream:
            category, amount = await self.process_transaction(transaction)
            transaction_count += 1
            
            # Вывод прогресса
            if transaction_count % 50 == 0:
                print(f"Обработано {transaction_count} транзакций")
        
        return transaction_count
    
    # Формирование сводки
    def get_summary(self) -> Dict[str, Any]:
        max_category = max(self.category_totals.items(), key=lambda x: x[1]) if self.category_totals else ("Нет данных", 0)
        min_category = min(self.category_totals.items(), key=lambda x: x[1]) if self.category_totals else ("Нет данных", 0)
        
        return {
            "total_categories": len(self.category_totals),
            "total_amount": sum(self.category_totals.values()),
            "max_category": {
                "name": max_category[0],
                "amount": max_category[1]
            },
            "min_category": {
                "name": min_category[0],
                "amount": min_category[1]
            },
            "category_details": [
                {
                    "category": category,
                    "total": total,
                    "transaction_count": len(self.category_transactions[category])
                }
                for category, total in sorted(self.category_totals.items(), key=lambda x: x[1], reverse=True)
            ]
        }
    
    # Сохранение результатов
    async def save_results(self, output_filename: str = "processing_results.json"):
        results = {
            "processed_at": datetime.now().isoformat(),
            "warning_threshold": self.warning_threshold,
            "summary": self.get_summary(),
            "category_totals": dict(self.category_totals)
        }
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"Результаты сохранены в {output_filename}")


async def main():
    if len(sys.argv) != 2:
        print("Использование: python process_transactions.py <файл_с_транзакциями>")
        print("Пример: python process_transactions.py all_transactions.json")
        return
    
    input_filename = sys.argv[1]
    
    processor = TransactionProcessor(warning_threshold=3000)
    
    # Обработка транзакций
    total_processed = await processor.process_stream(input_filename)
    
    print("-" * 50)
    print(f"Обработка завершена")
    print(f"Всего обработано транзакций: {total_processed}")
    print(f"Найдено категорий: {len(processor.category_totals)}")
    print()
    
    # Вывод результатов
    print("Расходы по категориям:")
    print("-" * 30)
    for category, total in sorted(processor.category_totals.items(), key=lambda x: x[1], reverse=True):
        count = len(processor.category_transactions[category])
        print(f"{category:15} | {total:10.2f} | {count:4} транзакций")
    
    print("-" * 30)
    print(f"Общая сумма: {sum(processor.category_totals.values()):.2f}")
    
    # Сохранение результатов
    await processor.save_results()


if __name__ == "__main__":
    asyncio.run(main())
    