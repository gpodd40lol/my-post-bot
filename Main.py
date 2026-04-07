import telebot
from telebot import types
from flask import Flask
from threading import Thread
import json
import os
import time

# --- НАСТРОЙКИ ---
MY_ID = 8337438678 
CHANNEL_ID = "@твой_канал" 
TOKEN = '8714339036:AAFXObv_yHVz0ydAL1ECAeVQ0eEAs2hoTCc'

bot = telebot.TeleBot(TOKEN)
app = Flask('')

user_data = {}

# --- БАЗА ДАННЫХ ---
DB_FILE = "justice_base.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "blacklist": []}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route('/')
def home(): return "Stealth Justice System Online"

# --- ФУНКЦИЯ ОЧИСТКИ ---
def clear_chat(chat_id, message_ids):
    for m_id in message_ids:
        try: bot.delete_message(chat_id, m_id)
        except: pass

@bot.message_handler(commands=['start'])
def start(message):
    db = load_db()
    uid = str(message.chat.id)
    if uid in db["blacklist"]: return

    # Проверка лимита 5 заявок в день
    today = time.strftime("%Y-%m-%d")
    user_info = db["users"].get(uid, {"count": 0, "date": ""})
    
    if user_info["date"] == today and user_info["count"] >= 5:
        bot.send_message(uid, "⚠️ Лимит: 5 заявок в день исчерпан. Ждем тебя завтра!")
        return

    m1 = bot.send_message(uid, "⚔️ **БАЗА ПОЗОРА**\n\n👤 **ШАГ 1:** Пришли Ник нарушителя:", parse_mode='Markdown')
    user_data[message.chat.id] = {"msg_to_delete": [message.message_id, m1.message_id]}
    bot.register_next_step_handler(message, get_nick)

def get_nick(message):
    cid = message.chat.id
    user_data[cid]['nick'] = message.text
    user_data[cid]['msg_to_delete'].append(message.message_id)
    
    m = bot.send_message(cid, "📝 **ШАГ 2:** Опиши, что он натворил:")
    user_data[cid]['msg_to_delete'].append(m.message_id)
    bot.register_next_step_handler(message, get_action)

def get_action(message):
    cid = message.chat.id
    user_data[cid]['action'] = message.text
    user_data[cid]['msg_to_delete'].append(message.message_id)
    
    m = bot.send_message(cid, "🔗 **ШАГ 3:** Пришли любые доп. данные или пруфы (текстом):")
    user_data[cid]['msg_to_delete'].append(m.message_id)
    bot.register_next_step_handler(message, submit_final)

def submit_final(message):
    cid = message.chat.id
    user_data[cid]['proofs'] = message.text
    user_data[cid]['msg_to_delete'].append(message.message_id)
    data = user_data[cid]

    admin_post = (
        f"🚨 **[ НОВЫЙ ОТЧЕТ ]**\n"
        f"👤 **НИК:** `{data['nick']}`\n"
        f"📜 **СУТЬ:** {data['action']}\n"
        f"🔍 **ДОП:** {data['proofs']}\n"
        f"👤 **ОТ:** @{message.from_user.username or 'Аноним'} (`{cid}`)"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ В КАНАЛ", callback_data=f"ok_{cid}"),
        types.InlineKeyboardButton("❌ ОТКАЗ", callback_data=f"no_{cid}")
    )
    
    bot.send_message(MY_ID, admin_post, parse_mode='Markdown', reply_markup=markup)
    
    # Обновляем счетчик юзера в базе
    db = load_db()
    today = time.strftime("%Y-%m-%d")
    if uid := str(cid):
        if db["users"].get(uid, {}).get("date") != today:
            db["users"][uid] = {"count": 1, "date": today}
        else:
            db["users"][uid]["count"] += 1
        save_db(db)

    bot.send_message(cid, "✅ **Отправлено!** История удалится через 5 сек.")
    time.sleep(5)
    clear_chat(cid, user_data[cid]['msg_to_delete'])

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    action, user_id = call.data.split('_')
    
    if action == "ok":
        bot.send_message(user_id, "📢 Твой отчет опубликован в канале базы!")
        bot.edit_message_text(f"{call.message.text}\n\n🟢 **ОДОБРЕНО**", chat_id=MY_ID, message_id=call.message.message_id)
        # Тут можно добавить bot.send_message(CHANNEL_ID, ...) для авто-постинга
        
    elif action == "no":
        bot.send_message(user_id, "❌ Отчет отклонен.")
        bot.edit_message_text(f"{call.message.text}\n\n🔴 **ОТКЛОНЕНО**", chat_id=MY_ID, message_id=call.message.message_id)

def run(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    Thread(target=run).start()
    bot.infinity_polling()
    
