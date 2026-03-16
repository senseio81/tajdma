import os
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# Прямая вставка токенов (замените на свои реальные токены)
BOT_TOKEN = "8729937825:AAH4pBjxa0T5RZz4ZJo_yqpQQvKpEhPeJio"  # ВАШ РЕАЛЬНЫЙ ТОКЕН
CRYPTO_TOKEN = "55871:AAroJKn4AgOhd3XcCt6dFDH5W2P9Ezac2Dd"  # ВАШ РЕАЛЬНЫЙ ТОКЕН CRYPTO PAY

# Проверка наличия токенов
if not BOT_TOKEN or BOT_TOKEN == "BOT_TOKEN":
    raise ValueError("Пожалуйста, замените BOT_TOKEN на реальный токен!")
if not CRYPTO_TOKEN or CRYPTO_TOKEN == "CRYPTO_TOKEN":
    raise ValueError("Пожалуйста, замените CRYPTO_TOKEN на реальный токен!")

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
        "amount": str(balance)  # Изменил на строку, если API требует
    }

    try:
        print(f"Отправка запроса: {data}")  # Для отладки
        r = requests.post(API_URL + "transfer", headers=headers, json=data)
        print(f"Ответ: {r.text}")  # Для отладки
        
        result = r.json()

        if result.get("ok"):
            user_balance[user_id] = 0
            await callback.message.answer("✅ Выплата отправлена")
        else:
            error_msg = result.get("error", "Неизвестная ошибка")
            await callback.message.answer(f"❌ Ошибка выплаты: {error_msg}")
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка соединения: {str(e)}")

if __name__ == "__main__":
    print("Бот запущен...")
    executor.start_polling(dp)
