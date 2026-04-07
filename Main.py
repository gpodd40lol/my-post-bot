import telebot
from flask import Flask
from threading import Thread

# 1. Настройки (ЗАПОЛНИ ИХ!)
MY_ID = 8337438678  # Твой цифровой ID (узнай его у бота @userinfobot)

bot = telebot.TeleBot('8714339036:AAFXObv_yHVz0ydAL1ECAeVQ0eEAs2hoTCc')
app = Flask('')

# Хранилище данных (временно)
user_data = {}

@app.route('/')
def home():
    return "Бот для постов запущен!"

def run():
    app.run(host='0.0.0.0', port=8080)

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Привет! Чтобы сделать пост, пришли мне Ник пользователя.")
    bot.register_next_step_handler(message, get_nick)

# Шаг 1: Получаем Ник
def get_nick(message):
    user_data[message.chat.id] = {'nick': message.text}
    bot.send_message(message.chat.id, "✅ Принято. Теперь пришли его ID:")
    bot.register_next_step_handler(message, get_id)

# Шаг 2: Получаем ID
def get_id(message):
    user_data[message.chat.id]['id_user'] = message.text
    bot.send_message(message.chat.id, "✅ Записал. А теперь опиши, что он сделал:")
    bot.register_next_step_handler(message, get_action)

# Шаг 3: Получаем описание и отправляем админу
def get_action(message):
    chat_id = message.chat.id
    user_data[chat_id]['action'] = message.text
    
    data = user_data[chat_id]
    
    # Формируем красивый текст поста
    post_text = (
        f"📢 **Новый пост!**\n\n"
        f"👤 **Ник:** {data['nick']}\n"
        f"🆔 **ID:** {data['id_user']}\n"
        f"📝 **Что сделал:** {data['action']}\n\n"
        f"Отправил: @{message.from_user.username or 'без юзернейма'}"
    )
    
    # Отправляем тебе (админу)
    bot.send_message(MY_ID, post_text, parse_mode='Markdown')
    
    # Подтверждение пользователю
    bot.send_message(chat_id, "🚀 Спасибо! Твой отчет отправлен админу на проверку.")

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
  
