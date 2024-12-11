import sqlite3
from datetime import datetime, time
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.ext import JobQueue

# Создаем базу данных для хранения информации о днях рождения
conn = sqlite3.connect("birthdays.db")
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS birthdays (
             user_id INTEGER, 
             username TEXT, 
             chat_id INTEGER,
             birthday DATE)''')
conn.commit()

# Функция для начала взаимодействия
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Привет! Я бот для поздравлений с днем рождения. Отправь мне свою дату рождения в формате DD-MM-YYYY.")

# Функция для записи дня рождения
async def save_birthday(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    chat_id = update.message.chat_id

    try:
        birthday = datetime.strptime(update.message.text, "%d-%m-%Y").date()
        c.execute("INSERT OR REPLACE INTO birthdays (user_id, username, chat_id, birthday) VALUES (?, ?, ?, ?)",
                  (user_id, username, chat_id, birthday))
        conn.commit()
        await update.message.reply_text("Ваш день рождения успешно сохранен!")
    except ValueError:
        await update.message.reply_text("Неправильный формат даты. Пожалуйста, используйте формат DD-MM-YYYY.")

# Функция для проверки и отправки поздравлений
async def check_birthdays(context: CallbackContext):
    bot: Bot = context.bot
    today = datetime.now().date()

    c.execute("SELECT username, chat_id FROM birthdays WHERE strftime('%m-%d', birthday) = ?", (today.strftime("%m-%d"),))
    results = c.fetchall()

    for username, chat_id in results:
        await bot.send_message(chat_id=chat_id, text=f"Сегодня день рождения у @{username}! Поздравляем!")

# Основная функция
if __name__ == "__main__":
    TOKEN = "TOKEN"
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("^\d{2}-\d{2}-\d{4}$"), save_birthday))

    # Создаем JobQueue вручную и запускаем задачу
    job_queue = JobQueue()
    job_queue.set_application(application)
    job_queue.run_daily(check_birthdays, time=time(hour=9))

    # Запускаем JobQueue и бота
    job_queue.start()
    application.run_polling()