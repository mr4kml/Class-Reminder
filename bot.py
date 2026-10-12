import asyncio
import json
import os
import logging
from datetime import datetime
from threading import Thread
from flask import Flask
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Grab token from Render Environment Variables securely
BOT_TOKEN = os.environ.get("BOT_TOKEN")
USERS_FILE = "users.json"

# Schedule Data Dictionary
DAILY_SCHEDULE = {
    0: """📚 **Monday Schedule**
- Breakout class (N) G1 - 001 | 9:00 - 10:00 am (Physics)
- Breakout class (Br) G6 - 004 | 9:00 - 10:00 am (Physics 1)
- Breakout class (B) G4 - 002 | 10:15 - 11:15 am (English 1)
- Breakout class (N) G2 - 001 | 10:15 - 11:15 am (Physics 1)
- Main class | 2:00 - 3:15 pm (Physics 1)
- Main class | 3:45 - 5:00 pm (Calculus 1)""",

    1: """📚 **Tuesday Schedule**
- Breakout class (B) G5 - 002 | 9:00 - 10:00 am (English 1)
- Breakout class (D) G4 - 005 | 9:00 - 10:00 am (Calculus 1)
- Breakout class (T) G1 - 001 | 9:00 - 10:00 am (Calculus 1)
- Breakout class (B) G6 - 002 | 10:15 - 11:15 am (English 1)
- Breakout class (D) G3 - 005 | 10:15 - 11:15 am (Calculus 1)
- Breakout class (T) G2 - 001 | 10:15 - 11:15 am (Calculus 1)
- Main class | 2:00 - 3:30 pm (English 1)""",

    2: """📚 **Wednesday Schedule**
- Breakout class (N) G3 - 001 | 9:00 - 10:00 am (Physics 1)
- Breakout class (Br) G5 - 004 | 9:00 - 10:00 am (Physics 1)
- Breakout class (S) G2 - 003 | 10:15 - 11:15 am (English 1)
- Breakout class (Br) G4 - 004 | 10:15 - 11:15 am (Physics 1)
- Main class | 2:00 - 3:15 pm (Physics 1)
- Main class | 3:45 - 5:00 pm (Calculus 1)""",

    3: """📚 **Thursday Schedule**
- Breakout class (S) G1 - 003 | 9:00 - 10:00 am (English 1)
- Breakout class (Z) G6 - 002 | 9:00 - 10:00 am (Calculus 1)
- Breakout class (S) G3 - 003 | 10:15 - 11:15 am (English 1)
- Breakout class (Z) G5 - 002 | 10:15 - 11:15 am (Calculus 1)
- Main class | 2:00 - 3:30 pm""",

    4: """📚 **Friday Schedule**
- Main class | 3:45 - 5:00 pm (Calculus 1)""",

    5: "🎉 **Saturday Schedule**\nNo classes today!",
    6: "🎉 **Sunday Schedule**\nNo classes today!"
}

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(list(users), f)

subscribers = load_users()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in subscribers:
        subscribers.add(chat_id)
        save_users(subscribers)
        logging.info(f"New subscriber added: {chat_id}")
    
    await update.message.reply_text(
        "👋 Welcome! You are now subscribed to the daily schedule reminders. You'll get your updates every morning at 7:00 AM!"
    )

async def send_schedule_to_all(bot: Bot):
    weekday = datetime.now().weekday()
    message = DAILY_SCHEDULE.get(weekday, "No schedule found.")
    
    for chat_id in subscribers:
        try:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
            logging.info(f"Schedule sent to {chat_id}")
        except Exception as e:
            logging.error(f"Failed to send to {chat_id}: {e}")

async def run_telegram_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_schedule_to_all, 'cron', hour=7, minute=0, args=[app.bot])
    scheduler.start()

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    logging.info("Telegram bot polling is active...")
    while True:
        await asyncio.sleep(3600)

# Flask app to satisfy Render's web service requirement
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is alive and running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Start Flask in a background thread
    t = Thread(target=run_flask)
    t.start()

    # Run the Telegram bot in the main thread
    asyncio.run(run_telegram_bot())