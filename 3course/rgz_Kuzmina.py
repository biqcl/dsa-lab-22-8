import asyncio
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import psycopg2
import aiohttp

# Конфигурация
API_TOKEN = os.getenv('API_TOKEN')
EXCHANGE_SERVER = "http://localhost:5000"  # Адрес Flask сервера

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Подключение к PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="finance_bot",
    user="postgres",
    password="postgres"
)
cur = conn.cursor()

# Состояния FSM
class RegistrationStates(StatesGroup):
    waiting_for_name = State()

class OperationStates(StatesGroup):
    waiting_for_type = State()
    waiting_for_amount = State()
    waiting_for_date = State()

class OperationsViewStates(StatesGroup):
    waiting_for_currency = State()

# Клавиатуры
def get_operation_type_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="РАСХОД"), KeyboardButton(text="ДОХОД")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_currency_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="RUB"), KeyboardButton(text="EUR"), KeyboardButton(text="USD")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# Проверка регистрации пользователя
async def is_user_registered(chat_id):
    cur.execute("SELECT 1 FROM users WHERE chat_id = %s", (chat_id,))
    return cur.fetchone() is not None

# Получение курса валют
async def get_exchange_rate(target_currency):
    if target_currency == "RUB":
        return 1.0
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{EXCHANGE_SERVER}/rate?currency={target_currency}") as response:
                if response.status == 200:
                    data = await response.json()
                    return data['rate']
                return None
    except:
        return None

# Обработчики команд

# /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Добро пожаловать в бот для учета финансов!\n"
        "Доступные команды:\n"
        "/reg - регистрация\n"
        "/add_operation - добавить операцию\n"
        "/operations - просмотр операций\n"
        "/lk - личный кабинет"
    )

# /reg
@dp.message(Command("reg"))
async def cmd_reg(message: types.Message, state: State):
    chat_id = message.chat.id
    
    if await is_user_registered(chat_id):
        await message.answer("Вы уже зарегистрированы!")
        return
    
    await message.answer("Введите ваше имя:")
    await state.set_state(RegistrationStates.waiting_for_name)

@dp.message(RegistrationStates.waiting_for_name)
async def process_name(message: types.Message, state: State):
    name = message.text
    chat_id = message.chat.id
    registration_date = datetime.now()
    
    try:
        cur.execute(
            "INSERT INTO users (chat_id, name, registration_date) VALUES (%s, %s, %s)",
            (chat_id, name, registration_date)
        )
        conn.commit()
        await message.answer(f"Регистрация успешно завершена, {name}!")
        await state.clear()
    except Exception as e:
        await message.answer("Произошла ошибка при регистрации. Попробуйте позже.")
        print(e)

# /add_operation
@dp.message(Command("add_operation"))
async def cmd_add_operation(message: types.Message, state: State):
    chat_id = message.chat.id
    
    if not await is_user_registered(chat_id):
        await message.answer("Вы не зарегистрированы! Используйте /reg")
        return
    
    await message.answer("Выберите тип операции:", reply_markup=get_operation_type_keyboard())
    await state.set_state(OperationStates.waiting_for_type)

@dp.message(OperationStates.waiting_for_type)
async def process_operation_type(message: types.Message, state: State):
    operation_type = message.text
    
    if operation_type not in ["РАСХОД", "ДОХОД"]:
        await message.answer("Пожалуйста, выберите тип операции используя кнопки.")
        return
    
    await state.update_data(operation_type=operation_type)
    await message.answer("Введите сумму операции в рублях:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(OperationStates.waiting_for_amount)

@dp.message(OperationStates.waiting_for_amount)
async def process_operation_amount(message: types.Message, state: State):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
        
        await state.update_data(amount=amount)
        await message.answer("Введите дату операции в формате ДД.ММ.ГГГГ (или /today для сегодняшней даты):")
        await state.set_state(OperationStates.waiting_for_date)
    except ValueError:
        await message.answer("Пожалуйста, введите положительное число.")

@dp.message(OperationStates.waiting_for_date)
async def process_operation_date(message: types.Message, state: State):
    date_str = message.text.lower()
    chat_id = message.chat.id
    today = datetime.now()
    
    try:
        if date_str == "/today":
            operation_date = today
        else:
            operation_date = datetime.strptime(date_str, "%d.%m.%Y")
            if operation_date > today:
                await message.answer("Дата операции не может быть позже сегодняшнего дня!")
                return
        
        data = await state.get_data()
        
        cur.execute(
            "INSERT INTO operations (date, amount, chat_id, operation_type) VALUES (%s, %s, %s, %s)",
            (operation_date, data['amount'], chat_id, data['operation_type'])
        )
        conn.commit()
        
        await message.answer(
            f"Операция добавлена:\n"
            f"Тип: {data['operation_type']}\n"
            f"Сумма: {data['amount']} RUB\n"
            f"Дата: {operation_date.strftime('%d.%m.%Y')}"
        )
        await state.clear()
    except ValueError:
        await message.answer("Неверный формат даты. Используйте ДД.ММ.ГГГГ или /today.")

# /operations
@dp.message(Command("operations"))
async def cmd_operations(message: types.Message, state: State):
    chat_id = message.chat.id
    
    if not await is_user_registered(chat_id):
        await message.answer("Вы не зарегистрированы! Используйте /reg")
        return
    
    await message.answer("Выберите валюту для отображения операций:", reply_markup=get_currency_keyboard())
    await state.set_state(OperationsViewStates.waiting_for_currency)

@dp.message(OperationsViewStates.waiting_for_currency)
async def process_operations_currency(message: types.Message, state: State):
    currency = message.text
    chat_id = message.chat.id
    
    if currency not in ["RUB", "EUR", "USD"]:
        await message.answer("Пожалуйста, выберите валюту используя кнопки.")
        return
    
    exchange_rate = await get_exchange_rate(currency)
    if exchange_rate is None:
        await message.answer("Не удалось получить курс валют. Попробуйте позже.")
        await state.clear()
        return
    
    cur.execute(
        "SELECT date, amount, operation_type FROM operations WHERE chat_id = %s ORDER BY date DESC",
        (chat_id,)
    )
    operations = cur.fetchall()
    
    if not operations:
        await message.answer("У вас пока нет операций.")
        await state.clear()
        return
    
    response = f"Ваши операции ({currency}):\n\n"
    total_income = 0
    total_expense = 0
    
    for op in operations:
        date = op[0].strftime("%d.%m.%Y")
        amount = float(op[1]) / exchange_rate  # Конвертируем из RUB в выбранную валюту
        op_type = op[2]
        
        if op_type == "ДОХОД":
            total_income += amount
            prefix = "+"
        else:
            total_expense += amount
            prefix = "-"
        
        response += f"{date} {op_type}: {prefix}{amount:.2f} {currency}\n"
    
    response += f"\nИтого доходы: {total_income:.2f} {currency}\n"
    response += f"Итого расходы: {total_expense:.2f} {currency}\n"
    response += f"Баланс: {total_income - total_expense:.2f} {currency}"
    
    await message.answer(response)
    await state.clear()

# /lk - личный кабинет
@dp.message(Command("lk"))
async def cmd_lk(message: types.Message):
    chat_id = message.chat.id
    
    if not await is_user_registered(chat_id):
        await message.answer("Вы не зарегистрированы! Используйте /reg")
        return
    
    # Получаем информацию о пользователе
    cur.execute(
        "SELECT name, registration_date FROM users WHERE chat_id = %s",
        (chat_id,)
    )
    user_info = cur.fetchone()
    
    # Получаем количество операций
    cur.execute(
        "SELECT COUNT(*) FROM operations WHERE chat_id = %s",
        (chat_id,)
    )
    operations_count = cur.fetchone()[0]
    
    response = (
        f"Личный кабинет\n\n"
        f"Имя: {user_info[0]}\n"
        f"Дата регистрации: {user_info[1].strftime('%d.%m.%Y')}\n"
        f"Количество операций: {operations_count}"
    )
    
    await message.answer(response)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    cur.close()
    conn.close()
    