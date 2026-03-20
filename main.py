import os
import logging
from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.constants import ParseMode  # ✅ Ключевое исправление
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

EMOJI_IDS = {
    "diamond": "5427168083074628963",
    "money": "5409048419211682843",
    "calendar": "5413879192267805083",
    "star": "5438496463044752972",
}

def format_emoji(emoji_char: str, emoji_id: str = None) -> str:
    if emoji_id:
        return f'<tg-emoji emoji-id="{emoji_id}">{emoji_char}</tg-emoji>'
    return emoji_char

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance FLOAT DEFAULT 0.0,
            turnover FLOAT DEFAULT 0.0,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            premium BOOLEAN DEFAULT FALSE,
            bonus_claimed BOOLEAN DEFAULT FALSE,
            promo_name TEXT,
            promo_bio TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def get_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def create_user(user_id, username, first_name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (user_id, username, first_name) VALUES (%s, %s, %s)",
        (user_id, username, first_name)
    )
    conn.commit()
    cur.close()
    conn.close()

def update_user_data(user_id, balance=None, turnover=None):
    conn = get_db_connection()
    cur = conn.cursor()
    if balance is not None:
        cur.execute("UPDATE users SET balance = %s WHERE user_id = %s", (balance, user_id))
    if turnover is not None:
        cur.execute("UPDATE users SET turnover = %s WHERE user_id = %s", (turnover, user_id))
    conn.commit()
    cur.close()
    conn.close()

def get_league(turnover):
    if turnover < 300:
        return ("👀", "Зритель", "5210956306952758910")
    elif turnover < 600:
        return ("⚡️", "Новичок", "5456140674028019486")
    else:
        return ("👑", "Профи", "5217822164362739968")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username
    first_name = user.first_name
    
    existing_user = get_user(user_id)
    if not existing_user:
        create_user(user_id, username, first_name)
    
    reply_keyboard = [["🎲 Играть", "🔐 Профиль"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f'<tg-emoji emoji-id="5461151367559141950">🎉</tg-emoji> Добро пожаловать, @{username}!',
        parse_mode=ParseMode.HTML,
        reply_markup=markup
    )

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = get_user(user_id)
    
    if not user_data:
        await update.message.reply_text("Ошибка. Напишите /start")
        return
    
    days = (date.today() - user_data["joined_at"].date()).days
    balance = user_data["balance"]
    turnover = user_data["turnover"]
    
    emoji, league_name, emoji_id = get_league(turnover)
    
    if turnover < 300:
        next_league = f"{300 - turnover} из 300"
    elif turnover < 600:
        next_league = f"{600 - turnover} из 600"
    else:
        next_league = "Максимальная лига достигнута 👑"
    
    diamond = format_emoji("💎", EMOJI_IDS["diamond"])
    money = format_emoji("💵", EMOJI_IDS["money"])
    calendar = format_emoji("🗓", EMOJI_IDS["calendar"])
    star = format_emoji("⭐️", EMOJI_IDS["star"])
    league_emoji = format_emoji(emoji, emoji_id)
    
    text = (
        f'{diamond} Ваш профиль ›\n'
        f'├ Баланс: {balance} {money}\n\n'
        f'{calendar} Вы с нами уже {days} дней\n\n'
        f'{star} Ваша лига: {league_emoji} {league_name}\n'
        f'├ Оборот: {turnover} {money}\n'
        f'└ До следующей лиги: {next_league} {money}'
    )
    
    keyboard = [
        [
            InlineKeyboardButton("💳 Пополнить", callback_data="deposit"),
            InlineKeyboardButton("📤 Вывести", callback_data="withdraw")
        ],
        [
            InlineKeyboardButton("💎 Акция 250$", callback_data="promo"),
            InlineKeyboardButton("🧩 Поддержка", url="https://t.me/MNGhotdice")
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)

async def handle_reply_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔐 Профиль":
        await update.message.reply_text("🔐", reply_to_message_id=update.message.message_id)
        await profile(update, context)
    elif text == "🎲 Играть":
        await update.message.reply_text("🚧 Игра в разработке")

async def handle_inline_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not query.data:
        return
    
    if query.data == "deposit":
        await query.edit_message_text("🚧 Пополнение в разработке")
    elif query.data == "withdraw":
        await query.edit_message_text("🚧 Вывод в разработке")
    elif query.data == "promo":
        promo_text = (
            "💎 Акция 250$\n\n"
            "💳 Хочешь зарабатывать на Hot Dice ежедневно, абсолютно ничего не делая кроме одного простого действия?\n\n"
            "Установи в свой ник — @Hot_DiceBot\n"
            "(пример: Ваш Ник | @Hot_DiceBot)\n\n"
            "И поставь в био — 🎲 250$+ в день сидя на диване, и играя в кубы - @Hot_Dicebot\n\n"
            "💎 И Вы получите:\n\n"
            "➡️ <b>+1% к кешбеку</b> (пока соблюдены правила)\n"
            "➡️ <b>+0.028x к коэффициенту</b> (пока соблюдены правила)\n"
            "➡️ <b>12.5$</b> рандомным 20-ти людям на CryptoBot ЕЖЕДНЕВНО\n\n"
            "Не пропусти возможность учавствовать! Просто вставь наш линк в ник и био, и лутай бабки ежедневно 💸\n"
            "— И не расстраивайся, если ты не выиграл сегодня, у тебя еще много шансов!"
        )
        keyboard = [[InlineKeyboardButton("✅ Участвовать", callback_data="join_promo")]]
        markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(promo_text, parse_mode=ParseMode.HTML, reply_markup=markup)
    elif query.data == "join_promo":
        user = update.effective_user
        user_id = user.id
        
        try:
            chat = await context.bot.get_chat(user_id)
            current_name = chat.first_name or user.first_name or ""
            current_bio = chat.bio or ""
        except Exception as e:
            logging.error(f"Ошибка получения данных чата: {e}")
            current_name = user.first_name or ""
            current_bio = ""
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE users 
            SET promo_name = %s, promo_bio = %s 
            WHERE user_id = %s
        """, (current_name, current_bio, user_id))
        conn.commit()
        cur.close()
        conn.close()
        
        await query.answer("✅ Вы участвуете в акции! Ваши данные сохранены.", show_alert=True)

def main():
    init_db()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text(["🔐 Профиль", "🎲 Играть"]), handle_reply_buttons))
    app.add_handler(CallbackQueryHandler(handle_inline_buttons))
    
    app.run_polling()

if __name__ == "__main__":
    main()
