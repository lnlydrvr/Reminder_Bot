from telethon import TelegramClient, events
import sqlite3
from datetime import datetime, time
import asyncio
from api_settings import *

# Настройка клиента бота
client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)
group_chat_id = None

# Запись ID группового чата
@client.on(events.ChatAction)
async def capture_group_id(event):
    global group_chat_id

    # Проверяем, если это групповое событие
    if event.is_group:
        group_chat_id = event.chat_id
        print(f"ID группы сохранен: {group_chat_id}")

        # Сохраняем ID в файл
        with open("group_id.txt", "w") as file:
            file.write(str(group_chat_id))

with open("group_id.txt", "r") as file:
    group_chat_id = int(file.read().strip())

# Настройка базы данных
db = sqlite3.connect('birthdays.db')
cursor = db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS birthdays (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    birthday DATE
)
""")
db.commit()

# Команда для установки дня рождения
@client.on(events.NewMessage(pattern='/set_birthday'))
async def set_birthday(event):
    try:
        args = event.message.text.split()
        if len(args) < 2:
            await event.reply('Укажите дату в формате: /set_birthday DD-MM-YYYY')
            return
        
        date = args[1]
        birthday = datetime.strptime(date, "%d-%m-%Y").date()
        user_id = event.sender_id
        username = event.sender.username or event.sender.first_name
        
        cursor.execute("REPLACE INTO birthdays (user_id, username, birthday) VALUES (?, ?, ?)", 
                       (user_id, username, birthday))
        db.commit()
        
        await event.reply(f"Дата рождения {birthday.strftime('%d-%m-%Y')} успешно сохранена!")
    
    except ValueError:
        await event.reply("Неверный формат даты. Используйте: /set_birthday DD-MM-YYYY")

# Функция для проверки и отправки уведомлений о днях рождения
async def check_birthdays():
    now = datetime.now()
    today = now.date()
    current_time = now.time()
    
    # Если текущее время не равно 7:00 утра, выходим
    if current_time != time(7, 0):
        return

    cursor.execute("SELECT username, birthday FROM birthdays")
    for username, birthday in cursor.fetchall():
        # Приводим дату рождения к текущему году
        next_birthday = datetime.strptime(birthday, "%Y-%m-%d").date().replace(year=today.year)
        if next_birthday == today:
            await client.send_message(
                group_chat_id,
                f"Сегодня день рождения у @{username}! 🎉"
            )

# Планировщик для регулярной проверки
async def scheduler():
    while True:
        await check_birthdays()
        await asyncio.sleep(60)  # Проверяем каждые 60 секунд

# Запуск бота
async def main():
    print("Бот запущен!")
    await client.start(bot_token=bot_token)

    # Запускаем планировщик в отдельной задаче
    asyncio.create_task(scheduler())

    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
