import os
import sys
from telebot import TeleBot
from openai import OpenAI

# 1. Проверяем наличие обязательных переменных окружения
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AI_API_KEY = os.getenv("AI_API_KEY")

if not BOT_TOKEN or not AI_API_KEY:
    print("Ошибка: Переменные TELEGRAM_BOT_TOKEN или AI_API_KEY не заданы!")
    sys.exit(1)

# 2. Инициализируем Телеграм-бота
bot = TeleBot(BOT_TOKEN)

# 3. Настраиваем подключение к серверам Google AI Studio через OpenAI SDK
ai_client = OpenAI(
    api_key=AI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Простейшая история сообщений (очищается при перезапуске контейнера)
chat_histories = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_histories[message.chat.id] = []
    bot.reply_to(message, "Привет! Я твой ИИ ассистент на базе Google Gemini. Задай мне любой вопрос!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    user_text = message.text

    if chat_id not in chat_histories:
        chat_histories[chat_id] = []

    # Сохраняем реплику пользователя
    chat_histories[chat_id].append({"role": "user", "content": user_text})
    
    # Ограничиваем историю последними 10 сообщениями
    chat_histories[chat_id] = chat_histories[chat_id][-10:]

    # Статус «печатает...» в Телеграме
    bot.send_chat_action(chat_id, 'typing')

    try:
        # Формируем контекст: системная инструкция + история чата
        messages_payload = [{"role": "system", "content": "Ты дружелюбный и полезный ИИ-помощник."}] + chat_histories[chat_id]

        # Запрос к нейросети (используется бесплатная базовая модель gemini-2.5-flash)
        response = ai_client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=messages_payload
        )
        
        ai_reply = response.choices[0].message.content
        
        # Сохраняем ответ ИИ в историю
        chat_histories[chat_id].append({"role": "assistant", "content": ai_reply})
        
        # Отвечаем пользователю в чат
        bot.reply_to(message, ai_reply)

    except Exception as e:
        print(f"Ошибка при запросе к Gemini API: {e}")
        bot.reply_to(message, "Извини, произошла внутренняя ошибка при обработке запроса к ИИ.")

if __name__ == "__main__":
    print("Бот успешно запущен и слушает сервер...")
    bot.infinity_polling()
