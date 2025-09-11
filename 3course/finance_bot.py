import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import psycopg2
from datetime import datetime
import aiohttp

API_TOKEN = os.getenv('API_TOKEN')
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

conn = psycopg2.connect(
    host="localhost",
    database="finance_bot",
    user="postgres",
    password="postgres"
)
cur = conn.cursor()

class FinanceStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_operation_type = State()
    waiting_for_amount = State()
    waiting_for_date = State()
    waiting_for_currency = State()

commands = [
    types.BotCommand(command="start", description="Начать работу"),
    types.BotCommand(command="reg", description="Регистрация"),
    types.BotCommand(command="add_operation", description="Добавить операцию"),
    types.BotCommand(command="operations", description="Просмотр операций")
]

async def setup_bot_commands():
    await bot.set_my_commands(commands)

async def is_registered(chat_id: int) -> bool:
    cur.execute("SELECT 1 FROM users WHERE chat_id = %s", (chat_id,))
    return cur.fetchone() is not None

async def get_currency_rate(currency: str) -> float:
    if currency == "RUB":
        return 1.0
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f'http://localhost:5000/rate?currency={currency}') as resp:
            if resp.status == 200:
                data = await resp.json()
                return data['rate']
            return 0.0

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Добро пожаловать в бот для учета финансов!\n"
        "Доступные команды:\n"
        "/reg - регистрация\n"
        "/add_operation - добавить операцию\n"
        "/operations - просмотр операций"
    )

@dp.message(Command("reg"))
async def cmd_reg(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    if await is_registered(chat_id):
        await message.answer("Вы уже зарегистрированы!")
        return
    await message.answer("Введите ваше имя:")
    await state.set_state(FinanceStates.waiting_for_name)

@dp.message(FinanceStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("Имя не может быть пустым!")
        return
    
    chat_id = message.chat.id
    try:
        cur.execute(
            "INSERT INTO users (chat_id, name) VALUES (%s, %s)",
            (chat_id, name)
        )
        conn.commit()
        await message.answer(f"Регистрация успешно завершена, {name}!")
        await state.clear()
    except:
        await message.answer("Ошибка при регистрации. Попробуйте позже.")
        await state.clear()

def get_operation_type_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="ДОХОД"), KeyboardButton(text="РАСХОД")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_currency_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="RUB"), KeyboardButton(text="EUR"), KeyboardButton(text="USD")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

@dp.message(Command("add_operation"))
async def cmd_add_operation(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    if not await is_registered(chat_id):
        await message.answer("Сначала зарегистрируйтесь с помощью команды /reg")
        return
    await message.answer("Выберите тип операции:", reply_markup=get_operation_type_keyboard())
    await state.set_state(FinanceStates.waiting_for_operation_type)

@dp.message(FinanceStates.waiting_for_operation_type)
async def process_operation_type(message: types.Message, state: FSMContext):
    operation_type = message.text.upper()
    if operation_type not in ["ДОХОД", "РАСХОД"]:
        await message.answer("Пожалуйста, выберите тип операции из предложенных вариантов")
        return
    await state.update_data(type_operation=operation_type)
    await message.answer("Введите сумму операции в рублях:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(FinanceStates.waiting_for_amount)

@dp.message(FinanceStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            await message.answer("Сумма должна быть положительной!")
            return
        await state.update_data(amount=amount)
        await message.answer("Введите дату операции в формате ДД.ММ.ГГГГ (или /today для сегодняшней даты):")
        await state.set_state(FinanceStates.waiting_for_date)
    except:
        await message.answer("Пожалуйста, введите число!")

@dp.message(Command("today"), FinanceStates.waiting_for_date)
async def cmd_today(message: types.Message, state: FSMContext):
    today = datetime.now().date()
    await state.update_data(date=today)
    await save_operation(message, state)

@dp.message(FinanceStates.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    try:
        date_str = message.text
        date = datetime.strptime(date_str, "%d.%m.%Y").date()
        
        if date > datetime.now().date():
            await message.answer("Дата операции не может быть позже сегодняшнего дня!")
            return
            
        await state.update_data(date=date)
        await save_operation(message, state)
    except:
        await message.answer("Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ")

async def save_operation(message: types.Message, state: FSMContext):
    data = await state.get_data()
    chat_id = message.chat.id
    
    try:
        cur.execute(
            "INSERT INTO operations (date, amount, chat_id, type_operation) VALUES (%s, %s, %s, %s)",
            (data["date"], data["amount"], chat_id, data["type_operation"])
        )
        conn.commit()
        await message.answer(
            f"Операция успешно добавлена!\n"
            f"Тип: {data['type_operation']}\n"
            f"Сумма: {data['amount']} RUB\n"
            f"Дата: {data['date'].strftime('%d.%m.%Y')}"
        )
        await state.clear()
    except:
        await message.answer("Ошибка при сохранении операции. Попробуйте позже.")
        await state.clear()

@dp.message(Command("operations"))
async def cmd_operations(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    if not await is_registered(chat_id):
        await message.answer("Сначала зарегистрируйтесь с помощью команды /reg")
        return
    
    cur.execute(
        "SELECT 1 FROM operations WHERE chat_id = %s LIMIT 1",
        (chat_id,)
    )
    if not cur.fetchone():
        await message.answer("У вас пока нет операций")
        return
    
    await message.answer("Выберите валюту для отображения операций:", reply_markup=get_currency_keyboard())
    await state.set_state(FinanceStates.waiting_for_currency)

@dp.message(FinanceStates.waiting_for_currency)
async def process_currency(message: types.Message, state: FSMContext):
    currency = message.text.upper()
    chat_id = message.chat.id
    
    if currency not in ["RUB", "EUR", "USD"]:
        await message.answer("Пожалуйста, выберите валюту из предложенных вариантов", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    rate = await get_currency_rate(currency)
    if rate == 0.0 and currency != "RUB":
        await message.answer("Не удалось получить курс валюты. Попробуйте позже.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    cur.execute(
        "SELECT date, amount, type_operation FROM operations WHERE chat_id = %s ORDER BY date DESC",
        (chat_id,)
    )
    operations = cur.fetchall()
    
    if not operations:
        await message.answer("У вас пока нет операций", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    total_income = 0.0
    total_expense = 0.0
    response = f"Ваши операции ({currency}):\n\n"
    total_income = 0
    total_expense = 0
    
    for op in operations:
        date = op[0].strftime("%d.%m.%Y")
        amount = float(op[1]) / rate  # Конвертируем из RUB в выбранную валюту
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

async def main():
    await setup_bot_commands()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    cur.close()
    conn.close()
