import telebot
from telebot import types # Добавили для кнопок
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
    
    tz_moscow = pytz.timezone('Europe/Moscow')
    current_time = datetime.now(tz_moscow).strftime("%d.%m.%Y | %H:%M")
    
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

    # Создаем кнопки для админа
    markup = types.InlineKeyboardMarkup()
    # В callback_data зашиваем действие и ID пользователя, чтобы бот знал кому отвечать
    btn_approve = types.InlineKeyboardButton("✅ Проверка пройдена", callback_data=f"accept_{chat_id}")
    btn_decline = types.InlineKeyboardButton("❌ Отказано", callback_data=f"decline_{chat_id}")
    markup.add(btn_approve, btn_decline)
    
    user_confirm = (
        "✅ **ОТЧЕТ ПРИНЯТ!**\n\n"
        "Твоя информация передана админу. Скоро пост появится в канале. \n\n"
        "🤝 *Спасибо за бдительность!*"
    )
    
    try:
        bot.send_message(MY_ID, admin_post, parse_mode='Markdown', reply_markup=markup)
        bot.send_message(chat_id, user_confirm, parse_mode='Markdown')
    except:
        bot.send_message(MY_ID, "Ошибка в верстке, проверь данные. Пост от " + str(chat_id), reply_markup=markup)

# Обработчик нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    # Разделяем команду и ID пользователя
    action, user_id = call.data.split('_')
    
    if action == "accept":
        bot.send_message(user_id, "✅ **Ваш пост прошел проверку и опубликован!**", parse_mode='Markdown')
        bot.edit_message_text(chat_id=MY_ID, message_id=call.message.message_id, 
                             text=call.message.text + "\n\n🟢 **ПРИНЯТО**", parse_mode='Markdown')
        
    elif action == "decline":
        bot.send_message(user_id, "❌ **Ваш пост отклонен модератором.**", parse_mode='Markdown')
        bot.edit_message_text(chat_id=MY_ID, message_id=call.message.message_id, 
                             text=call.message.text + "\n\n🔴 **ОТКЛОНЕНО**", parse_mode='Markdown')

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
    
