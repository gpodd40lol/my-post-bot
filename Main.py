import telebot
from telebot import types
from flask import Flask
from threading import Thread
import json
import os
import time
import random

# --- НАСТРОЙКИ ---
MY_ID = 8337438678 
CHANNEL_ID = "@твой_канал" # Замени на свой
TOKEN = '8714339036:AAFXObv_yHVz0ydAL1ECAeVQ0eEAs2hoTCc'

bot = telebot.TeleBot(TOKEN)
app = Flask('')

user_data = {}
DB_FILE = "justice_hardcore.json"

# --- СИСТЕМА БАЗЫ ---
def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "blacklist": [], "total_cases": 0, "tickets": {}, "history_nicks": []}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route('/')
def home(): return "Justice System v11.0 Hardcore Online"

# --- АДМИН-КОМАНДЫ ---
@bot.message_handler(commands=['stats'])
def stats(message):
    if message.chat.id == MY_ID:
        db = load_db()
        bot.send_message(MY_ID, f"📊 **СТАТИСТИКА:**\n\n👤 Юзеров: {len(db['users'])}\n📝 Дел: {db['total_cases']}\n🚫 В бане: {len(db['blacklist'])}")

@bot.message_handler(commands=['send'])
def broadcast(message):
    if message.chat.id == MY_ID:
        text = message.text.replace('/send', '').strip()
        db = load_db()
        for u in db["users"]:
            try: bot.send_message(u, f"📢 **СООБЩЕНИЕ:**\n{text}")
            except: pass

@bot.message_handler(commands=['unban'])
def unban(message):
    if message.chat.id == MY_ID:
        uid = message.text.replace('/unban', '').strip()
        db = load_db()
        if uid in db["blacklist"]:
            db["blacklist"].remove(uid)
            save_db(db)
            bot.send_message(MY_ID, f"✅ Юзер {uid} разбанен.")

# --- ПОДАЧА ЖАЛОБЫ ---
@bot.message_handler(commands=['start'])
def start(message):
    db = load_db()
    uid = str(message.chat.id)
    if uid in db["blacklist"]: return

    if uid not in db["users"]:
        db["users"][uid] = {"fails": 0, "reports_today": 0, "last_date": ""}
    
    # Лимит 5 в день
    today = time.strftime("%Y-%m-%d")
    if db["users"][uid]["last_date"] == today and db["users"][uid]["reports_today"] >= 5:
        bot.send_message(uid, "⚠️ Лимит 5 жалоб в день!")
        return
    
    save_db(db)
    m = bot.send_message(uid, "⚔️ **БАЗА ПОЗОРА**\n\n👤 **ШАГ 1:** Ник нарушителя:")
    user_data[uid] = {"msgs": [message.message_id, m.message_id]}
    bot.register_next_step_handler(message, get_nick)

def get_nick(message):
    uid = str(message.chat.id)
    nick = message.text
    db = load_db()
    
    # Репутация (проверка дублей)
    rep = db["history_nicks"].count(nick.lower())
    user_data[uid]['nick'] = nick
    user_data[uid]['rep'] = rep
    user_data[uid]['msgs'].append(message.message_id)
    
    m = bot.send_message(uid, f"📝 **ШАГ 2:** Опиши деяние `{nick}`:")
    user_data[uid]['msgs'].append(m.message_id)
    bot.register_next_step_handler(message, get_action)

def get_action(message):
    uid = str(message.chat.id)
    user_data[uid]['action'] = message.text
    user_data[uid]['msgs'].append(message.message_id)
    
    data = user_data[uid]
    tid = str(random.randint(10000, 99999))
    db = load_db()
    
    db["tickets"][tid] = {"uid": uid, "nick": data['nick'], "action": data['action'], "status": "ожидание"}
    save_db(db)

    rep_text = f"\n⚠️ **ПОВТОР:** Был в базе {data['rep']} раз!" if data['rep'] > 0 else ""
    admin_post = (
        f"🎟 **ТИКЕТ #{tid}**{rep_text}\n"
        f"👤 **НИК:** `{data['nick']}`\n"
        f"📜 **СУТЬ:** {data['action']}\n"
        f"👤 **ОТ:** @{message.from_user.username or 'Аноним'} (`{uid}`)\n"
        f"⚠️ **КОСЯКИ ЮЗЕРА:** {db['users'][uid]['fails']}/3"
    )

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ В КАНАЛ", callback_data=f"ok_{tid}"),
        types.InlineKeyboardButton("❌ ОТКАЗ", callback_data=f"no_{tid}"),
        types.InlineKeyboardButton("🚫 БАН", callback_data=f"ban_{uid}"),
        types.InlineKeyboardButton("✉️ ОТВЕТ", callback_data=f"msg_{uid}")
    )
    
    bot.send_message(MY_ID, admin_post, parse_mode='Markdown', reply_markup=markup)
    bot.send_message(uid, f"✅ **ПРИНЯТО!** Тикет: `#{tid}`\nСтелс-очистка через 5 сек...")
    
    time.sleep(5)
    for m_id in user_data[uid]['msgs']:
        try: bot.delete_message(uid, m_id)
        except: pass

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    db = load_db()
    action, val = call.data.split('_')
    
    if action == "ok":
        t = db["tickets"].get(val)
        if t:
            db["total_cases"] += 1
            num = db["total_cases"]
            # ВИЗУАЛЬНАЯ КАРТОЧКА
            card = (
                f"🔥 **ЛИЧНОЕ ДЕЛО №{num}** 🔥\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 **ЦЕЛЬ:** `{t['nick']}`\n"
                f"📜 **ДЕЯНИЕ:** {t['action']}\n"
                f"📅 **ДАТА:** {time.strftime('%d.%m.%Y')}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"⚖️ СТАТУС: **ОПУБЛИКОВАНО**"
            )
            bot.send_message(CHANNEL_ID, card, parse_mode='Markdown')
            
            db["history_nicks"].append(t["nick"].lower())
            db["users"][t["uid"]]["reports_today"] += 1
            db["users"][t["uid"]]["last_date"] = time.strftime("%Y-%m-%d")
            db["users"][t["uid"]]["fails"] = 0
            t["status"] = "принят"
            save_db(db)
            bot.send_message(t["uid"], f"✅ Твой пост опубликован под №{num}!")
        bot.edit_message_text(f"{call.message.text}\n\n🟢 **ОДОБРЕНО**", chat_id=MY_ID, message_id=call.message.message_id)

    elif action == "no":
        t = db["tickets"].get(val)
        if t:
            db["users"][t["uid"]]["fails"] += 1
            if db["users"][t["uid"]]["fails"] >= 3:
                db["blacklist"].append(t["uid"])
                bot.send_message(t["uid"], "⛔️ Авто-бан за 3 отказа.")
            else:
                bot.send_message(t["uid"], f"❌ Отчет #{val} отклонен.")
            save_db(db)
        bot.edit_message_text(f"{call.message.text}\n\n🔴 **ОТКЛОНЕНО**", chat_id=MY_ID, message_id=call.message.message_id)

    elif action == "msg":
        bot.send_message(MY_ID, "✍️ Ответ юзеру (анонимно):")
        bot.register_next_step_handler(call.message, lambda m: bot.send_message(val, f"💬 **ОТВЕТ АДМИНА:**\n{m.text}"))

    elif action == "ban":
        db["blacklist"].append(val)
        save_db(db)
        bot.send_message(val, "⛔️ Ты забанен.")
        bot.edit_message_text(f"{call.message.text}\n\n🚫 **ЗАБАНЕН**", chat_id=MY_ID, message_id=call.message.message_id)

def run(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    Thread(target=run).start()
    bot.infinity_polling()
    
