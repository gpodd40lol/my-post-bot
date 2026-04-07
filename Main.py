import telebot
from flask import Flask
from threading import Thread
from datetime import datetime # Добавил для времени

# Настройки
MY_ID = 8337438678 
bot = telebot.TeleBot('8714339036:AAFXObv_yHVz0ydAL1ECAeVQ0eEAs2hoTCc')
app = Flask('')

user_data = {}

@app.route('/')
def home():
    return "Бот для постов активен!"

def run():
    app.run(host='0.0.0.0', port=8080)

@bot.message_handler(commands=['start'])
def start(message):
    user_data[message.chat.id] = {} 
    bot.send_message(message.chat.id, "👋 Начинаем оформление поста.\n\n👤 Пришли **Ник** нарушителя:")
    bot.register_next_step_handler(message, get_nick)

def get_nick(message):
    if message.text == '/start': return start(message)
    user_data[message.chat.id]['nick'] = message.text
    bot.send_message(message.chat.id, "📝 Теперь опиши, **что он сделал**:")
    bot.register_next_step_handler(message, get_action)

def get_action(message):
    if message.text == '/start': return start(message)
    
    chat_id = message.chat.id
    user_data[chat_id]['action'] = message.text
    data = user_data[chat_id]
    
    # Моя добавка: автоматическая дата и статус
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    post_text = (
        f"🚨 **НОВЫЙ ПОСТ В ОЧЕРЕДЬ** 🚨\n"
        f"━━━━━━━━━━━━━━\n"
        f"👤 **Нарушитель:** {data['nick']}\n"
        f"📜 **Суть:** {data['action']}\n"
        f"📅 **Дата фиксации:** {current_time}\n"
        f"⚙️ **Статус:** Ожидает проверки\n"
        f"━━━━━━━━━━━━━━\n"
        f"👤 **Отправил:** @{message.from_user.username or 'скрыто'}"
    )
    
    # Пытаемся отправить сообщение ТЕБЕ
    try:
        bot.send_message(MY_ID, post_text, parse_mode='Markdown')
        bot.send_message(chat_id, "✅ Готово! Твой пост улетел админу.")
    except Exception as e:
        # Если Markdown сломается, отправим обычным текстом
        bot.send_message(MY_ID, post_text.replace('*', ''))
        bot.send_message(chat_id, "🚀 Пост отправлен (упрощенная версия).")

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
    
