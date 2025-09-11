import asyncio
import os
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters.command import Command
import psycopg2
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, BotCommand, BotCommandScopeDefault, BotCommandScopeChat

# Конфигурация
API_TOKEN = os.getenv('API_TOKEN')
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# URL микросервисов
CURRENCY_MANAGER_URL = "http://localhost:5001"
DATA_MANAGER_URL = "http://localhost:5002"
ROLE_MANAGER_URL = "http://localhost:5003"

# Подключение к БД
conn = psycopg2.connect(
    host = "localhost",
    database = "rpp_database",
    user = "postgres",
    password = "postgres"
)
cur = conn.cursor()

# Состояния FSM
class CurrencyStates(StatesGroup):
    waiting_for_manage_action = State()
    waiting_for_add_name = State()
    waiting_for_add_rate = State()
    waiting_for_delete_name = State()
    waiting_for_update_name = State()
    waiting_for_update_rate = State()
    waiting_for_convert_currency = State()
    waiting_for_convert_amount = State()

# Команды бота
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
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ROLE_MANAGER_URL}/admins") as response:
                if response.status == 200:
                    data = await response.json()
                    admin_chat_ids = data.get("admins", [])
                    for chat_id in admin_chat_ids:
                        await bot.set_my_commands(
                            admin_commands, 
                            scope=BotCommandScopeChat(chat_id=chat_id)
                        )
    except:
        pass

# Функция проверки администратора
async def is_admin(chat_id):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{ROLE_MANAGER_URL}/is_admin",
                params={"chat_id": chat_id}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("is_admin", False)
                return False
    except:
        return False

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    chat_id = str(message.from_user.id)
    
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
        await message.answer("Неизвестное действие. Пожалуйста, используйте кнопки.")


# Обработчики для добавления валюты
@dp.message(CurrencyStates.waiting_for_add_name)
async def process_add_name(message: types.Message, state: State):
    currency_name = message.text.upper()
    await state.update_data(currency_name=currency_name)
    await message.answer("Введите курс к рублю:")
    await state.set_state(CurrencyStates.waiting_for_add_rate)


@dp.message(CurrencyStates.waiting_for_add_rate)
async def process_add_rate(message: types.Message, state: State):
    try:
        rate = float(message.text)
        data = await state.get_data()
        currency_name = data["currency_name"]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{CURRENCY_MANAGER_URL}/load",
                json={"currency_name": currency_name, "rate": rate}
            ) as response:
                if response.status == 200:
                    await message.answer(f"Валюта: {currency_name} успешно добавлена")
                elif response.status == 400:
                    response_data = await response.json()
                    await message.answer(response_data.get("error", "Ошибка при добавлении валюты"))
                else:
                    await message.answer("Ошибка при добавлении валюты")
        
        await state.clear()
    except ValueError:
        await message.answer("Ошибка! Введите число.")


# Обработчик для удаления валюты
@dp.message(CurrencyStates.waiting_for_delete_name)
async def process_delete_name(message: types.Message, state: State):
    currency_name = message.text.upper()
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{CURRENCY_MANAGER_URL}/delete",
            json={"currency_name": currency_name}
        ) as response:
            if response.status == 200:
                await message.answer(f"Валюта {currency_name} успешно удалена")
            elif response.status == 404:
                await message.answer(f"Валюта {currency_name} не найдена")
            else:
                await message.answer("Ошибка при удалении валюты")
    
    await state.clear()


# Обработчики для изменения курса валюты
@dp.message(CurrencyStates.waiting_for_update_name)
async def process_update_name(message: types.Message, state: State):
    currency_name = message.text.upper()
    await state.update_data(currency_name=currency_name)
    await message.answer("Введите новый курс к рублю:")
    await state.set_state(CurrencyStates.waiting_for_update_rate)


@dp.message(CurrencyStates.waiting_for_update_rate)
async def process_update_rate(message: types.Message, state: State):
    try:
        rate = float(message.text)
        data = await state.get_data()
        currency_name = data["currency_name"]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{CURRENCY_MANAGER_URL}/update_currency",
                json={"currency_name": currency_name, "new_rate": rate}
            ) as response:
                if response.status == 200:
                    await message.answer(f"Курс валюты {currency_name} успешно изменён на {rate}")
                elif response.status == 404:
                    await message.answer(f"Валюта {currency_name} не найдена")
                else:
                    await message.answer("Ошибка при обновлении курса валюты")
        
        await state.clear()
    except ValueError:
        await message.answer("Ошибка! Введите число.")


# Команда /get_currencies
@dp.message(Command("get_currencies"))
async def cmd_get_currencies(message: types.Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{DATA_MANAGER_URL}/currencies") as response:
            if response.status == 200:
                data = await response.json()
                currencies = data.get("currencies", [])
                
                if not currencies:
                    await message.answer("Нет сохранённых валют.")
                    return
                
                response_text = "Список доступных валют:\n"
                for currency in currencies:
                    response_text += f"{currency['currency']}: {currency['rate']} RUB\n"
                
                await message.answer(response_text)
            else:
                await message.answer("Ошибка при получении списка валют")


# Команда /convert
@dp.message(Command("convert"))
async def cmd_convert(message: types.Message, state: State):
    await message.answer("Введите название или код валюты")
    await state.set_state(CurrencyStates.waiting_for_convert_currency)


# Обработчик валюты для конвертации
@dp.message(CurrencyStates.waiting_for_convert_currency)
async def process_convert_currency(message: types.Message, state: State):
    currency_name = message.text.upper()
    await state.update_data(currency_name=currency_name)
    await message.answer(f"Введите сумму в {currency_name} для конвертации в рубли:")
    await state.set_state(CurrencyStates.waiting_for_convert_amount)


# Обработчик ввода суммы и вывод результата
@dp.message(CurrencyStates.waiting_for_convert_amount)
async def process_convert_amount(message: types.Message, state: State):
    try:
        amount = float(message.text)
        data = await state.get_data()
        currency_name = data["currency_name"]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{DATA_MANAGER_URL}/convert",
                params={"currency": currency_name, "amount": amount}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    await message.answer(
                        f"{result['original_amount']} {result['currency']} = "
                        f"{result['converted_amount']} {result['target_currency']}"
                    )
                elif response.status == 404:
                    await message.answer("Валюта не найдена")
                else:
                    await message.answer("Ошибка при конвертации валюты")
        
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите число")


async def main():
    await setup_bot_commands(bot)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
    cur.close()
    conn.close()
