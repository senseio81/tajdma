import os
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

BOT_TOKEN = os.getenv("BOT_TOKEN")
CRYPTO_TOKEN = os.getenv("CRYPTO_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

API_URL = "https://testnet-pay.crypt.bot/api/"

headers = {
    "Crypto-Pay-API-Token": CRYPTO_TOKEN
}

@dp.message_handler(commands=["start"])
async def start(message: types.Message):

    data = {
        "asset": "USDT",
        "amount": "1",
        "description": "Test payment"
    }

    r = requests.post(API_URL + "createInvoice", headers=headers, json=data)

    result = r.json()["result"]
    pay_url = result["bot_invoice_url"]

    await message.answer(f"💰 Test invoice\n\nPay here:\n{pay_url}")

if __name__ == "__main__":
    executor.start_polling(dp)
