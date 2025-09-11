import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, BotCommand, BotCommandScopeDefault, BotCommandScopeChat
import psycopg2


# Получение токена из переменного окружения
API_TOKEN = os.getenv('API_TOKEN')
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

conn = psycopg2.connect(
    host = "localhost",
    database = "rpp_database",
    user = "postgres",
    password = "postgres"
)
cur = conn.cursor()

# Словарь для хранения курсов валют
currencies = {}


# Состояния FSM
class CurrencyStates(StatesGroup):
    waiting_for_currency_name = State()
    waiting_for_currency_rate = State()
    waiting_for_convert_currency = State()
    waiting_for_convert_amount = State()

    waiting_for_manage_action = State()
    waiting_for_add_name = State()
    waiting_for_add_rate = State()
    waiting_for_delete_name = State()
    waiting_for_update_name = State()
    waiting_for_update_rate = State()

admin_commands = [
            BotCommand(command="start", description="Начать работу с ботом"),
            BotCommand(command="manage_currency", description="Управление валютами"),
            BotCommand(command="get_currencies", description="Список всех валют"),
            BotCommand(command="convert", description="Конвертация валют"),
        ]

user_commands = [
            BotCommand(command="start", description="Начать работу с ботом"),
            BotCommand(command="get_currencies", description="Список всех валют"),
            BotCommand(command="convert", description="Конвертация валют"),
        ]

# Функция для установки команд бота
async def setup_bot_commands(bot: Bot):
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
    
    cur.execute("SELECT chat_id FROM admins")
    admin_chat_ids = [row[0] for row in cur.fetchall()]
    for chat_id in admin_chat_ids:
        await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=chat_id))


# Функция проверки администратора
async def is_admin(chat_id):
    cur.execute("SELECT 1 FROM admins WHERE chat_id = %s", (chat_id,))
    return cur.fetchone() is not None


# Обработчики команд:

# /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    chat_id = str(message.from_user.id)
    print(f"Ваш chat_id: {chat_id}")
    
    # Проверяем, является ли пользователь администратором
    if await is_admin(chat_id):
        await message.answer(
            "Вы вошли как администратор.\n"
            "Доступные команды:\n"
            "- управление валютами\n"
            "- список всех валют\n"
            "- конвертация валют в рубли"
        )
    else:
        await message.answer(
            "Это бот для конвертации валют.\n"
            "Доступные команды:\n"
            "- список всех валют\n"
            "- конвертация валют в рубли"
        )


# /convert
@dp.message(Command("convert"))
async def cmd_convert(message: types.Message, state: State):
    cur.execute("SELECT EXISTS(SELECT 1 FROM currencies)")
    exists = cur.fetchone()[0]
    
    if not exists:
        await message.answer("Нет сохранённых валют. Сначала используйте /save_currency.")
        return
    
    await message.answer("Введите название валюты для конвертации:")
    await state.set_state(CurrencyStates.waiting_for_convert_currency)


# Обработчик ввода валюты для конвертации
@dp.message(CurrencyStates.waiting_for_convert_currency)
async def process_convert_currency(message: types.Message, state: State):
    currency_name = message.text.upper()
    
    cur.execute("SELECT rate FROM currencies WHERE currency_name = %s", (currency_name,))
    result = cur.fetchone()
    
    if not result:
        await message.answer("Эта валюта не найдена. Попробуйте ещё раз или используйте /get_currencies для списка доступных валют.")
        return
    
    rate = result[0]
    await state.update_data(currency_name=currency_name, rate=rate)
    await message.answer(f"Введите сумму в {currency_name} для конвертации в рубли:")
    await state.set_state(CurrencyStates.waiting_for_convert_amount)


# Обработчик ввода суммы и вывод результата
@dp.message(CurrencyStates.waiting_for_convert_amount)
async def process_convert_amount(message: types.Message, state: State):
    try:
        amount = float(message.text)
        data = await state.get_data()
        currency_name = data["currency_name"]
        rate = float(data["rate"])
        
        result = amount * rate
        await message.answer(f"{amount} {currency_name} = {result:.2f} RUB")
        await state.clear()
    
    except ValueError:
        await message.answer("Вы не ввели число!")


# Обработчик суммы и вывод результата
@dp.message(CurrencyStates.waiting_for_convert_amount)
async def process_convert_amount(message: types.Message, state: State):
    try:
        amount = float(message.text)
        data = await state.get_data()
        currency_name = data["currency_name"]
        rate = currencies[currency_name]
        result = amount * rate
        await message.answer(f"{amount} {currency_name} = {result:.2f} RUB")
        await state.clear()
    except ValueError:
        await message.answer("Вы не ввели число!")


# Клавиатура для управления валютами
def get_manage_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Добавить валюту"),
                KeyboardButton(text="Удалить валюту"),
                KeyboardButton(text="Изменить курс валюты"),
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


# Команда /manage_currency
@dp.message(Command("manage_currency"))
async def cmd_manage_currency(message: types.Message, state: State):
    if not await is_admin(str(message.from_user.id)):
        await message.answer("Нет доступа к команде")
        return
    
    await message.answer(
        "Выберите действие:",
        reply_markup=get_manage_keyboard()
    )
    await state.set_state(CurrencyStates.waiting_for_manage_action)


# Обработчик выбора действия
@dp.message(CurrencyStates.waiting_for_manage_action)
async def process_manage_action(message: types.Message, state: State):
    action = message.text.lower()
    
    if action == "добавить валюту":
        await message.answer("Введите название валюты:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(CurrencyStates.waiting_for_add_name)
    
    elif action == "удалить валюту":
        await message.answer("Введите название валюты:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(CurrencyStates.waiting_for_delete_name)
    
    elif action == "изменить курс валюты":
        await message.answer("Введите название валюты:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(CurrencyStates.waiting_for_update_name)
    
    else:
        await message.answer("Такой команды нет. Используйте меню команд.")


# Обработчики для добавления валюты
@dp.message(CurrencyStates.waiting_for_add_name)
async def process_add_name(message: types.Message, state: State):
    currency_name = message.text.upper()
    
    cur.execute("SELECT 1 FROM currencies WHERE currency_name = %s", (currency_name,))
    if cur.fetchone() is not None:
        await message.answer("Данная валюта уже существует")
        await state.clear()
        return
    
    await state.update_data(currency_name=currency_name)
    await message.answer("Введите курс к рублю:")
    await state.set_state(CurrencyStates.waiting_for_add_rate)


@dp.message(CurrencyStates.waiting_for_add_rate)
async def process_add_rate(message: types.Message, state: State):
    try:
        rate = float(message.text)
        data = await state.get_data()
        currency_name = data["currency_name"]
        
        cur.execute(
            "INSERT INTO currencies (currency_name, rate) VALUES (%s, %s)",
            (currency_name, rate)
        )
        conn.commit()
        
        currencies[currency_name] = rate  # Обновляем локальный словарь
        await message.answer(f"Валюта: {currency_name} успешно добавлена")
        await state.clear()
    except ValueError:
        await message.answer("Вы не ввели число!")


# Обработчик для удаления валюты
@dp.message(CurrencyStates.waiting_for_delete_name)
async def process_delete_name(message: types.Message, state: State):
    currency_name = message.text.upper()
    
    cur.execute(
        "DELETE FROM currencies WHERE currency_name = %s RETURNING currency_name",
        (currency_name,)
    )
    deleted = cur.fetchone()
    conn.commit()
    
    if deleted:
        currencies.pop(currency_name, None)  # Удаляем из локального словаря
        await message.answer(f"Валюта {currency_name} успешно удалена")
    else:
        await message.answer(f"Валюта {currency_name} не найдена")
    
    await state.clear()


# Обработчики для изменения курса валюты
@dp.message(CurrencyStates.waiting_for_update_name)
async def process_update_name(message: types.Message, state: State):
    currency_name = message.text.upper()
    
    cur.execute("SELECT 1 FROM currencies WHERE currency_name = %s", (currency_name,))
    if cur.fetchone() is None:
        await message.answer("Данная валюта не существует")
        await state.clear()
        return
    
    await state.update_data(currency_name=currency_name)
    await message.answer("Введите новый курс к рублю:")
    await state.set_state(CurrencyStates.waiting_for_update_rate)


@dp.message(CurrencyStates.waiting_for_update_rate)
async def process_update_rate(message: types.Message, state: State):
    try:
        rate = float(message.text)
        data = await state.get_data()
        currency_name = data["currency_name"]
        
        cur.execute(
            "UPDATE currencies SET rate = %s WHERE currency_name = %s",
            (rate, currency_name)
        )
        conn.commit()
        
        currencies[currency_name] = rate  # Обновляем локальный словарь
        await message.answer(f"Курс валюты {currency_name} успешно изменён на {rate}")
        await state.clear()
    except ValueError:
        await message.answer("Вы не ввели число!")


# Команда /get_currencies
@dp.message(Command("get_currencies"))
async def cmd_get_currencies(message: types.Message):
    cur.execute("SELECT currency_name, rate FROM currencies ORDER BY currency_name")
    records = cur.fetchall()
    
    if not records:
        await message.answer("Нет сохранённых валют.")
        return
    
    response = "Список доступных валют:\n"
    for currency in records:
        response += f"{currency[0]}: {currency[1]} RUB\n"
    
    await message.answer(response)


# Запуск бота
async def main():
    await setup_bot_commands(bot)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    cur.close()
    conn.close()
