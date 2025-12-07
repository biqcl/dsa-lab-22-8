import asyncio
import json
import random
from datetime import datetime
from typing import List, Dict, Any
import sys


class TransactionGenerator:
    def __init__(self):
        self.categories = [
            "food", "transport", "entertainment", 
            "utilities", "shopping", "health", 
            "education", "housing", "travel", "other"
        ]
        self.transaction_count = 0
        self.file_counter = 1
        
    # Генерация одной транзакции
    async def generate_transaction(self) -> Dict[str, Any]:
        await asyncio.sleep(0.01)  # Имитация асинхронной работы
        
        return {
            "timestamp": datetime.now().isoformat(),
            "category": random.choice(self.categories),
            "amount": round(random.uniform(10, 1000), 2)
        }
    
    # Асинхронный поток транзакций
    async def transaction_stream(self, num_transactions: int):
        for i in range(num_transactions):
            transaction = await self.generate_transaction()
            self.transaction_count += 1
            yield transaction
    
    # Обработка потока пакетами
    async def batch_processor(self, transactions_stream, batch_size: int = 10):
        batch = []
        
        async for transaction in transactions_stream:
            batch.append(transaction)
            
            if len(batch) >= batch_size:
                await self.save_batch(batch)
                batch = []
        
        # Оставшиеся транзакции
        if batch:
            await self.save_batch(batch)
    
    # Сохранение пакета транзакций
    async def save_batch(self, batch: List[Dict[str, Any]]):
        filename = f"transactions_batch_{self.file_counter}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(batch, f, indent=2, ensure_ascii=False)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
              f"Сохранен пакет {self.file_counter}: "
              f"{len(batch)} транзакций в файл {filename}")
        
        # Обновление основного файла
        await self.update_main_file(batch)
        
        self.file_counter += 1
    
    # Обновление файла со всеми транзакциями
    async def update_main_file(self, batch: List[Dict[str, Any]]):
        main_filename = "all_transactions.json"
        
        try:
            with open(main_filename, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            all_data = []
        
        all_data.extend(batch)
        
        with open(main_filename, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)


async def main():
    if len(sys.argv) != 2:
        print("Использование: python generate_transactions.py <количество_транзакций>")
        print("Пример: python generate_transactions.py 100")
        return
    
    try:
        num_transactions = int(sys.argv[1])
        if num_transactions <= 0:
            print("Количество транзакций должно быть положительным числом")
            return
    except ValueError:
        print("Пожалуйста, введите целое число")
        return
    
    print(f"Начало генерации {num_transactions} транзакций...")
    print("-" * 50)
    
    generator = TransactionGenerator()
    
    # Создание потока транзакций
    stream = generator.transaction_stream(num_transactions)
    
    # Обработка потока
    await generator.batch_processor(stream)
    
    print("-" * 50)
    print(f"Генерация завершена!")
    print(f"Создано файлов: {generator.file_counter - 1}")
    print(f"Все транзакции сохранены в all_transactions.json")


if __name__ == "__main__":
    asyncio.run(main())