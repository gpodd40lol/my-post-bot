import telebot
from telebot import types
from flask import Flask
from threading import Thread
import json
import os
import time

# --- НАСТРОЙКИ ---
MY_ID = 8337438678 
CHANNEL_ID = "@POZOR_OXIDE" 
TOKEN = '8714339036:AAFXObv_yHVz0ydAL1ECAeVQ0eEAs2hoTCc'

bot = telebot.TeleBot(TOKEN)
app = Flask('')

user_data = {}

# --- БАЗА ДАННЫХ (JSON) ---
DB_FILE = "justice_ultra.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "blacklist": [], "history": [], "admins": [MY_ID]}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Функция поиска повторок
def check_rep(nick):
    db = load_db()
    count = 0
    for h in db["history"]:
        if h["nick"].lower() == nick.lower():
            count += 1
    return count

@app.route('/')
def home(): return "Ultra Justice Engine Online"

# --- ПОДАЧА ЖАЛОБЫ ---
@bot.message_handler(commands=['start'])
def start(message):
    db = load_db()
    uid = str(message.chat.id)
    if uid in db["blacklist"]: return

    # Проверка лимита 5/день
    today = time.strftime("%Y-%m-%d")
    user_info = db["users"].get(uid, {"count": 0, "date": today})
    
    if user_info["date"] == today and user_info["count"] >= 5:
        bot.send_message(uid, "⚠️ Лимит на сегодня (5/5) исчерпан.")
        return

    m = bot.send_message(uid, "⚔️ **БАЗА ПОЗОРА**\n\n👤 **ШАГ 1:** Напиши НИК нарушителя:")
    user_data[message.chat.id] = {"msg_to_delete": [message.message_id, m.message_id]}
    bot.register_next_step_handler(message, get_nick)

def get_nick(message):
    cid = message.chat.id
    nick = message.text
    rep_count = check_rep(nick)
    
    user_data[cid]['nick'] = nick
    user_data[cid]['msg_to_delete'].append(message.message_id)
    
    # Если уже был в базе, предупреждаем админа позже, а юзеру просто пишем след. шаг
    m = bot.send_message(cid, f"📝 **ШАГ 2:** Что натворил `{nick}`?")
    user_data[cid]['msg_to_delete'].append(m.message_id)
    bot.register_next_step_handler(message, get_action)

def get_action(message):
    cid = message.chat.id
    user_data[cid]['action'] = message.text
    user_data[cid]['msg_to_delete'].append(message.message_id)
    m = bot.send_message(cid, "🔗 **ШАГ 3:** Любые пруфы или подробности:")
    user_data[cid]['msg_to_delete'].append(m.message_id)
    bot.register_next_step_handler(message, submit_final)

def submit_final(message):
    cid = message.chat.id
    user_data[cid]['proofs'] = message.text
    user_data[cid]['msg_to_delete'].append(message.message_id)
    data = user_data[cid]
    db = load_db()

    rep = check_rep(data['nick'])
    rep_text = f"\n⚠️ **ПОВТОР:** Этот ник уже был в базе {rep} раз!" if rep > 0 else ""

    admin_post = (
        f"🚨 **[ НОВЫЙ ОТЧЕТ ]**{rep_text}\n"
        f"👤 **НИК:** `{data['nick']}`\n"
        f"📜 **СУТЬ:** {data['action']}\n"
        f"🔍 **ДОП:** {data['proofs']}\n"
        f"👤 **ОТ:** @{message.from_user.username or 'Аноним'} (`{cid}`)"
    )

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ В КАНАЛ", callback_data=f"pub_{cid}"),
        types.InlineKeyboardButton("❌ ОТКАЗАТЬ", callback_data=f"rej_{cid}"),
        types.InlineKeyboardButton("🚫 БАН", callback_data=f"ban_{cid}")
    )
    
    bot.send_message(MY_ID, admin_post, parse_mode='Markdown', reply_markup=markup)
    
    # Счётчик лимита
    today = time.strftime("%Y-%m-%d")
    uid = str(cid)
    if uid not in db["users"] or db["users"][uid]["date"] != today:
        db["users"][uid] = {"count": 1, "date": today}
    else:
        db["users"][uid]["count"] += 1
    save_db(db)

    bot.send_message(cid, "✅ **Принято!** История чата сотрется через 5 сек.")
    time.sleep(5)
    for m_id in user_data[cid]['msg_to_delete']:
        try: bot.delete_message(cid, m_id)
        except: pass

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    db = load_db()
    action, user_id = call.data.split('_')
    
    if action == "pub":
        # Тут мы вытаскиваем ник из текста сообщения админу (между ` `)
        try:
            nick_start = call.message.text.find('`') + 1
            nick_end = call.message.text.find('`', nick_start)
            nick = call.message.text[nick_start:nick_end]
            
            # Сохраняем в историю одобренных
            db["history"].append({"nick": nick, "date": time.strftime("%d.%m.%Y")})
            save_db(db)
            
            bot.send_message(user_id, "🚀 **Твой отчет одобрен и опубликован!**")
            bot.edit_message_text(f"{call.message.text}\n\n🟢 **ОДОБРЕНО И ВНЕСЕНО В ИСТОРИЮ**", chat_id=MY_ID, message_id=call.message.message_id)
        except:
            bot.send_message(MY_ID, "Ошибка при парсинге ника.")

    elif action == "rej":
        # Быстрые кнопки причин для админа
        rmk = types.InlineKeyboardMarkup()
        rmk.add(types.InlineKeyboardButton("Нет пруфов", callback_data=f"reason_1_{user_id}"),
                types.InlineKeyboardButton("Флуд", callback_data=f"reason_2_{user_id}"))
        bot.edit_message_reply_markup(MY_ID, call.message.message_id, reply_markup=rmk)

    elif action == "reason":
        # Обработка причины (формат callback: reason_№_userid)
        r_type, u_id = call.data.split('_')[1], call.data.split('_')[2]
        reasons = {"1": "недостаточно доказательств", "2": "флуд/оффтоп"}
        bot.send_message(u_id, f"❌ **Отчет отклонен.** Причина: {reasons.get(r_type)}")
        bot.edit_message_text("🔴 **ОТКЛОНЕНО (Причина отправлена)**", chat_id=MY_ID, message_id=call.message.message_id)

    elif action == "ban":
        db["blacklist"].append(user_id)
        save_db(db)
        bot.send_message(user_id, "⛔️ Ты забанен.")
        bot.edit_message_text("🚫 **ЗАБАНЕН**", chat_id=MY_ID, message_id=call.message.message_id)

def run(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    Thread(target=run).start()
    bot.infinity_polling()
    
