# bot.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
from datetime import datetime
import os

# Токен вашего бота - УКАЖИТЕ В ПЕРЕМЕННОЙ ОКРУЖЕНИЯ НА RENDER
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# URL вашего веб-приложения на Render - ЗАМЕНИТЕ НА ВАШ
WEBAPP_URL = os.environ.get('WEBAPP_URL') or "https://ваш-проект.onrender.com/webapp"

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_choices (
            user_id INTEGER,
            username TEXT,
            selected_number INTEGER,
            timestamp TEXT,
            PRIMARY KEY (user_id)
        )
    ''')
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1", callback_data="1")],
        [InlineKeyboardButton("2", callback_data="2")],
        [InlineKeyboardButton("3", callback_data="3")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите число:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_number = int(query.data)
    user_id = query.from_user.id
    username = query.from_user.username or f"user_{user_id}"
    
    # Сохраняем выбор в базу данных
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO user_choices (user_id, username, selected_number, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, selected_number, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    # Добавляем user_id к URL
    web_app_url = f"{WEBAPP_URL}?user_id={user_id}"

    keyboard = [
        [InlineKeyboardButton("Открыть веб-приложение", web_app=WebAppInfo(url=web_app_url))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(
        f"Вы выбрали число: {selected_number}. Нажмите кнопку ниже, чтобы открыть веб-приложение.",
        reply_markup=reply_markup
    )

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()