import telebot
from flask import Flask
from threading import Thread
from datetime import datetime
import pytz

# Настройки
MY_ID = 8337438678 
bot = telebot.TeleBot('8714339036:AAFXObv_yHVz0ydAL1ECAeVQ0eEAs2hoTCc')
app = Flask('')

user_data = {}

@app.route('/')
def home():
    return "Бот активен"

def run():
    app.run(host='0.0.0.0', port=8080)

@bot.message_handler(commands=['start'])
def start(message):
    user_data[message.chat.id] = {} 
    # Добавил про читеров в приветствие
    welcome_text = (
        "⚔️ **ДОБРО ПОЖАЛОВАТЬ В БАЗУ ПОЗОРА** ⚔️\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Нашел крысу, нарушителя или читера? Слей его здесь.\n\n"
        "👤 **ШАГ 1:** Пришли мне Ник персонажа:"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')
    bot.register_next_step_handler(message, get_nick)

def get_nick(message):
    if message.text == '/start': return start(message)
    user_data[message.chat.id]['nick'] = message.text
    bot.send_message(message.chat.id, "📝 **ШАГ 2:** Теперь опиши его **деяние**:", parse_mode='Markdown')
    bot.register_next_step_handler(message, get_action)

def get_action(message):
    if message.text == '/start': return start(message)
    
    chat_id = message.chat.id
    user_data[chat_id]['action'] = message.text
    data = user_data[chat_id]
    
    # Настройка МСК времени
    tz_moscow = pytz.timezone('Europe/Moscow')
    current_time = datetime.now(tz_moscow).strftime("%d.%m.%Y | %H:%M")
    
    # Твой любимый шаблон (Админ-панель)
    admin_post = (
        f"🚨 **[ НОВЫЙ ПОСТ В ОЧЕРЕДЬ ]** 🚨\n"
        f"┣━━━━━━━━━━━━━━━━━━━━━\n"
        f"┃ 👤 **НАРУШИТЕЛЬ:** `{data['nick']}`\n"
        f"┃ 📜 **СУТЬ:** {data['action']}\n"
        f"┃ 📅 **ДАТА:** {current_time} (МСК)\n"
        f"┣━━━━━━━━━━━━━━━━━━━━━\n"
        f"┃ 👤 **ОТПРАВИЛ:** @{message.from_user.username or 'Аноним'}\n"
        f"┃ ⚙️ **СТАТУС:** *Ожидает проверки...*\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━"
    )
    
    # Ответ юзеру
    user_confirm = (
        "✅ **ОТЧЕТ ПРИНЯТ!**\n\n"
        "Твоя информация передана админу. Скоро пост появится в канале. \n\n"
        "🤝 *Спасибо за бдительность!*"
    )
    
    try:
        bot.send_message(MY_ID, admin_post, parse_mode='Markdown')
        bot.send_message(chat_id, user_confirm, parse_mode='Markdown')
    except:
        bot.send_message(MY_ID, admin_post.replace('*', '').replace('`', ''))
        bot.send_message(chat_id, "✅ Готово! Пост улетел админу.")

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
    
