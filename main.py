import os
from dotenv import load_dotenv
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

load_dotenv()  # Загружаем переменные из .env

BOT_TOKEN = os.getenv("BOT_TOKEN")
CRYPTO_TOKEN = os.getenv("CRYPTO_TOKEN")

# Проверка наличия токенов
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения!")
if not CRYPTO_TOKEN:
    raise ValueError("CRYPTO_TOKEN не найден в переменных окружения!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

API_URL = "https://testnet-pay.crypt.bot/api/"

headers = {
    "Crypto-Pay-API-Token": CRYPTO_TOKEN
}

# тестовый баланс
user_balance = {}

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_balance[message.from_user.id] = 5  # тестовый баланс

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("💸 Вывод", callback_data="withdraw"))

    await message.answer(
        f"Ваш баланс: {user_balance[message.from_user.id]} USDT",
        reply_markup=kb
    )

@dp.callback_query_handler(lambda c: c.data == "withdraw")
async def withdraw(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    balance = user_balance.get(user_id, 0)

    if balance <= 0:
        await callback.message.answer("❌ Баланс пуст")
        return

    data = {
        "user_id": user_id,
        "asset": "USDT",
        "amount": balance
    }

    try:
        r = requests.post(API_URL + "transfer", headers=headers, json=data)
        result = r.json()

        if result.get("ok"):
            user_balance[user_id] = 0
            await callback.message.answer("✅ Выплата отправлена")
        else:
            error_msg = result.get("error", "Неизвестная ошибка")
            await callback.message.answer(f"❌ Ошибка выплаты: {error_msg}")
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка соединения: {e}")

if __name__ == "__main__":
    executor.start_polling(dp)
