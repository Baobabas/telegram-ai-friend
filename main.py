import os
import google.generativeai as genai

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("AI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

# ===== ПАМЯТЬ =====
user_memory = {}

# ===== ПЕРСОНАЖИ =====
PERSONAS = {
    "👤 Друг": "Ты дружелюбный собеседник. Общайся нормально и естественно.",
    "😎 Бро": "Ты уверенный, спокойный друг. Говоришь кратко, по делу, с лёгким сленгом.",
    "🤪 Алкаш": "Ты немного пьяный весёлый собеседник. Шутки, разговорный стиль, юмор.",
    "🚜 Колхозник": "Ты простой деревенский мужик. Говоришь просто, с юмором и жизненно."
}

def get_model(user_id):
    persona = user_memory.get(user_id, {}).get("persona", "👤 Друг")

    return genai.GenerativeModel(
        "gemini-2.5-flash",
        system_instruction=PERSONAS[persona]
    )

def get_history(user_id):
    if user_id not in user_memory:
        user_memory[user_id] = {"history": [], "persona": "👤 Друг"}

    return user_memory[user_id]["history"]

# ===== КНОПКИ =====
def main_menu():
    return ReplyKeyboardMarkup(
        [
            ["👤 Друг", "😎 Бро"],
            ["🤪 Алкаш", "🚜 Колхозник"],
            ["🧹 Сброс"]
        ],
        resize_keyboard=True
    )

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет 👋 Я твой AI-друг. Выбери режим или просто пиши сообщения.",
        reply_markup=main_menu()
    )

# ===== ТЕКСТ =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    # переключение режима
    if text in PERSONAS:
        user_memory[user_id] = {
            "history": [],
            "persona": text
        }
        await update.message.reply_text(f"Режим изменён: {text}")
        return

    if text == "🧹 Сброс":
        user_memory[user_id] = {"history": [], "persona": "👤 Друг"}
        await update.message.reply_text("История очищена.")
        return

    history = get_history(user_id)
    model = get_model(user_id)

    # добавляем сообщение пользователя
    history.append(f"User: {text}")

    # ограничение памяти
    history = history[-10:]
    user_memory[user_id]["history"] = history

    try:
        prompt = "\n".join(history)

        response = model.generate_content(prompt)

        answer = response.text

        history.append(f"AI: {answer}")
        user_memory[user_id]["history"] = history

        await update.message.reply_text(answer)

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# ===== MAIN =====
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    print("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
