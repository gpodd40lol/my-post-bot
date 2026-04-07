import telebot
from telebot import types
from flask import Flask
from threading import Thread
from datetime import datetime
import os

# --- НАСТРОЙКИ ---
MY_ID = 8337438678 
TOKEN = '8714339036:AAFXObv_yHVz0ydAL1ECAeVQ0eEAs2hoTCc'

bot = telebot.TeleBot(TOKEN)
app = Flask('')

user_data = {}

# --- РАБОТА С БАЗОЙ ЮЗЕРОВ ---
def get_users():
    if not os.path.exists("users.txt"): return set()
    with open("users.txt", "r") as f:
        return set(line.strip() for line in f)

def add_user(user_id):
    users = get_users()
    if str(user_id) not in users:
        with open("users.txt", "a") as f:
            f.write(f"{user_id}\n")

def get_blacklist():
    if not os.path.exists("blacklist.txt"): return set()
    with open("blacklist.txt", "r") as f:
        return set(line.strip() for line in f)

def add_to_blacklist(user_id):
    with open("blacklist.txt", "a") as f:
        f.write(f"{user_id}\n")

# Настройка команд в меню
bot.set_my_commands([
    types.BotCommand("start", "🚀 Запустить бота / Подать жалобу"),
    types.BotCommand("info", "📝 Правила подачи")
])

@app.route('/')
def home(): return "Бот в строю"

# Рассылка от админа
@bot.message_handler(commands=['send'])
def broadcast(message):
    if message.chat.id == MY_ID:
        text = message.text.replace('/send', '').strip()
        if not text:
            bot.send_message(MY_ID, "❌ Введи текст: `/send Текст рассылки`", parse_mode='Markdown')
            return
        
        users = get_users()
        count = 0
        for user in users:
            try:
                bot.send_message(user, f"📢 **СООБЩЕНИЕ ОТ АДМИНИСТРАЦИИ:**\n\n{text}", parse_mode='Markdown')
                count += 1
            except: pass
        bot.send_message(MY_ID, f"✅ Рассылка завершена. Получили: {count} чел.")

@bot.message_handler(commands=['info'])
def info_cmd(message):
    bot.send_message(message.chat.id, "🛡 **ПРАВИЛА БАЗЫ ПОЗОРА:**\n\n1. Пиши только правду.\n2. Указывай точный ник.\n3. За ложные доносы — БАН.")

@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.chat.id)
    if uid in get_blacklist():
        bot.send_message(uid, "⛔️ Доступ закрыт.")
        return
    
    add_user(uid) # Сохраняем в базу для рассылки
    if message.chat.id != MY_ID:
        bot.send_message(MY_ID, f"🆕 Новый юзер в боте: @{message.from_user.username or 'Аноним'} (`{uid}`)")

    user_data[message.chat.id] = {} 
    bot.send_message(message.chat.id, "⚔️ **ШАГ 1:** Напиши НИК нарушителя:")
    bot.register_next_step_handler(message, get_nick)

def get_nick(message):
    if message.text.startswith('/'): return
    user_data[message.chat.id]['nick'] = message.text
    bot.send_message(message.chat.id, "📝 **ШАГ 2:** Опиши, что он сделал:")
    bot.register_next_step_handler(message, get_action)

def get_action(message):
    if message.text.startswith('/'): return
    chat_id = message.chat.id
    user_data[chat_id]['action'] = message.text
    data = user_data[chat_id]
    
    admin_post = (
        f"🚨 **[ НОВЫЙ ОТЧЕТ ]**\n"
        f"👤 **НИК:** `{data['nick']}`\n"
        f"📜 **СУТЬ:** {data['action']}\n"
        f"👤 **ОТ:** @{message.from_user.username or 'Аноним'} (`{chat_id}`)"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ ОДОБРИТЬ", callback_data=f"ok_{chat_id}"),
        types.InlineKeyboardButton("❌ ОТКАЗАТЬ", callback_data=f"no_{chat_id}"),
        types.InlineKeyboardButton("🚫 В БАН", callback_data=f"ban_{chat_id}")
    )
    
    bot.send_message(MY_ID, admin_post, parse_mode='Markdown', reply_markup=markup)
    bot.send_message(chat_id, "⌛️ **Принято!** Ожидайте решения админа.")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    action, user_id = call.data.split('_')
    
    if action == "ok":
        bot.send_message(user_id, "✅ **Ваша жалоба подтверждена!**")
        bot.edit_message_text(f"{call.message.text}\n\n🟢 **СТАТУС: ПОДТВЕРЖДЕНО**", chat_id=MY_ID, message_id=call.message.message_id)
        
    elif action == "no":
        bot.send_message(user_id, "❌ **Жалоба отклонена модератором.**")
        bot.edit_message_text(f"{call.message.text}\n\n🔴 **СТАТУС: ОТКЛОНЕНО**", chat_id=MY_ID, message_id=call.message.message_id)

    elif action == "ban":
        add_to_blacklist(user_id)
        bot.send_message(user_id, "⛔️ Ты заблокирован.")
        bot.edit_message_text(f"{call.message.text}\n\n🚫 **ПОЛЬЗОВАТЕЛЬ ЗАБАНЕН**", chat_id=MY_ID, message_id=call.message.message_id)

def run(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    Thread(target=run).start()
    bot.infinity_polling()
    
