import os
import requests
import time
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# Вставьте свои реальные токены
BOT_TOKEN = "8729937825:AAH4pBjxa0T5RZz4ZJo_yqpQQvKpEhPeJio"
CRYPTO_TOKEN = "55871:AAroJKn4AgOhd3XcCt6dFDH5W2P9Ezac2Dd"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

API_URL = "https://testnet-pay.crypt.bot/api/"

headers = {
    "Crypto-Pay-API-Token": CRYPTO_TOKEN
}

# тестовый баланс пользователей
user_balance = {}
# хранилище использованных spend_id
used_spend_ids = set()

def generate_spend_id():
    """Генерирует уникальный spend_id"""
    # Комбинация timestamp и случайного числа
    timestamp = int(time.time() * 1000)
    random_part = random.randint(1000, 9999)
    spend_id = f"{timestamp}{random_part}"
    return spend_id

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_balance[message.from_user.id] = 5  # тестовый баланс

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("💸 Вывод", callback_data="withdraw"))

    await message.answer(
        f"Ваш баланс: {user_balance[message.from_user.id]} USDT\n"
        f"ID пользователя: {message.from_user.id}",
        reply_markup=kb
    )

@dp.message_handler(commands=["balance"])
async def check_balance(message: types.Message):
    balance = user_balance.get(message.from_user.id, 0)
    await message.answer(f"Ваш баланс: {balance} USDT")

@dp.callback_query_handler(lambda c: c.data == "withdraw")
async def withdraw(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    balance = user_balance.get(user_id, 0)

    if balance <= 0:
        await callback.message.answer("❌ Баланс пуст")
        return

    # Генерируем уникальный spend_id
    spend_id = generate_spend_id()
    
    # Проверяем, не использовался ли уже такой spend_id
    while spend_id in used_spend_ids:
        spend_id = generate_spend_id()
    
    used_spend_ids.add(spend_id)

    data = {
        "user_id": str(user_id),  # Конвертируем в строку
        "asset": "USDT",
        "amount": str(balance),  # Конвертируем в строку
        "spend_id": spend_id,  # Обязательный параметр
        "description": f"Вывод средств для пользователя {user_id}"  # Опционально
    }

    await callback.message.answer("⏳ Обработка запроса на вывод...")

    try:
        print(f"Отправка запроса: {data}")
        print(f"Headers: {headers}")
        
        r = requests.post(API_URL + "transfer", headers=headers, json=data)
        print(f"Ответ: {r.text}")
        print(f"Статус код: {r.status_code}")
        
        result = r.json()

        if result.get("ok"):
            user_balance[user_id] = 0
            await callback.message.answer(
                f"✅ Выплата отправлена!\n"
                f"Сумма: {balance} USDT\n"
                f"ID транзакции: {spend_id}"
            )
        else:
            error = result.get("error", {})
            error_name = error.get("name") if isinstance(error, dict) else error
            error_desc = result.get("description", "Неизвестная ошибка")
            
            # Если ошибка из-за spend_id, удаляем его из использованных
            if error_name == "SPEND_ID_REQUIRED":
                used_spend_ids.discard(spend_id)
            
            await callback.message.answer(
                f"❌ Ошибка выплаты\n"
                f"Код: {error_name}\n"
                f"Описание: {error_desc}"
            )
    except Exception as e:
        used_spend_ids.discard(spend_id)  # Удаляем spend_id в случае ошибки
        await callback.message.answer(f"❌ Ошибка соединения: {str(e)}")

@dp.message_handler(commands=["help"])
async def help_command(message: types.Message):
    help_text = """
    Доступные команды:
    /start - начать работу
    /balance - проверить баланс
    /help - показать это сообщение
    
    Для вывода средств нажмите кнопку "💸 Вывод"
    """
    await message.answer(help_text)

if __name__ == "__main__":
    print("Бот запущен...")
    print(f"API URL: {API_URL}")
    print("Ожидание команд...")
    executor.start_polling(dp)
