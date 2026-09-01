import re
import json
import os
from collections import defaultdict
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
DATA_FILE = "sums.json"

user_sums = defaultdict(float)
user_names = {}

def load_data():
    global user_sums, user_names
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                user_sums = defaultdict(float, {int(k): v for k, v in data.get("sums", {}).items()})
                user_names = {int(k): v for k, v in data.get("names", {}).items()}
        except Exception:
            pass

def save_data():
    data = {
        "sums": {str(k): v for k, v in user_sums.items()},
        "names": {str(k): v for k, v in user_names.items()}
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def extract_first_number(text: str):
    text = text.strip().replace(',', '.')
    match = re.match(r'^(-?\d+\.?\d*)', text)
    if match:
        return float(match.group(1))
    return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_sums, user_names

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user = update.effective_user
    user_id = user.id
    name = user.full_name or user.username or str(user_id)

    user_names[user_id] = name

    if text.upper() == "ПОДСЧЕТ":
        if not user_sums:
            await update.message.reply_text("Пока ничего не посчитано.")
            return

        lines = ["📊 Результаты подсчёта:\n"]
        total = 0.0

        for uid, amount in sorted(user_sums.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"• {user_names.get(uid, uid)}: {amount:g}")
            total += amount

        lines.append(f"\n💰 Общая сумма: {total:g}")
        await update.message.reply_text("\n".join(lines))

        user_sums.clear()
        save_data()
        return

    number = extract_first_number(text)
    if number is not None:
        user_sums[user_id] += number
        save_data()

def main():
    load_data()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен и работает...")
    app.run_polling()

if __name__ == "__main__":
    main()
