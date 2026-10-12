import asyncio
import json
import os
import logging
from datetime import datetime
from threading import Thread
from flask import Flask
from telegram import Update, Bot, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
USERS_FILE = "users.json"

# Complete schedule with all breakout and main class professors
DAILY_SCHEDULE = {
    0: (
        "📚 **MONDAY SCHEDULE**\n\n"
        "🔸 **Breakout Classes (Morning):**\n"
        "  • 09:00 - 10:00 am | Physics - Dr. Nebiyu (G1 - 001)\n"
        "  • 09:00 - 10:00 am | Physics 1 - Bruhanu (G6 - 004)\n"
        "  • 10:15 - 11:15 am | English 1 - Dr. Bereket (G4 - 002)\n"
        "  • 10:15 - 11:15 am | Physics 1 - Dr. Nebiyu (G2 - 001)\n\n"
        "🔸 **Main Classes (Afternoon):**\n"
        "  • 2:00 - 3:15 pm | Physics 1 - Prof. Solomon Bililign\n"
        "  • 3:45 - 5:00 pm | Calculus 1 - Prof. Abdulkadir Hassen"
    ),
    1: (
        "📚 **TUESDAY SCHEDULE**\n\n"
        "🔸 **Breakout Classes (Morning):**\n"
        "  • 09:00 - 10:00 am | English 1 - Dr. Bereket (G5 - 002)\n"
        "  • 09:00 - 10:00 am | Calculus 1 - Dr. Demisse (G4 - 005)\n"
        "  • 09:00 - 10:00 am | Calculus 1 - Dr. Tekalign (G1 - 001)\n"
        "  • 10:15 - 11:15 am | English 1 - Dr. Bereket (G6 - 002)\n"
        "  • 10:15 - 11:15 am | Calculus 1 - Dr. Demisse (G3 - 005)\n"
        "  • 10:15 - 11:15 am | Calculus 1 - Dr. Tekalign (G2 - 001)\n\n"
        "🔸 **Main Classes (Afternoon):**\n"
        "  • 2:00 - 3:30 pm | English 1 - Prof. Karen Sichler"
    ),
    2: (
        "📚 **WEDNESDAY SCHEDULE**\n\n"
        "🔸 **Breakout Classes (Morning):**\n"
        "  • 09:00 - 10:00 am | Physics 1 - Dr. Nebiyu (G3 - 001)\n"
        "  • 09:00 - 10:00 am | Physics 1 - Bruhanu (G5 - 004)\n"
        "  • 10:15 - 11:15 am | English 1 - Dr. Sintayehu (G2 - 003)\n"
        "  • 10:15 - 11:15 am | Physics 1 - Bruhanu (G4 - 004)\n\n"
        "🔸 **Main Classes (Afternoon):**\n"
        "  • 2:00 - 3:15 pm | Physics 1 - Prof. Solomon Bililign\n"
        "  • 3:45 - 5:00 pm | Calculus 1 - Prof. Abdulkadir Hassen"
    ),
    3: (
        "📚 **THURSDAY SCHEDULE**\n\n"
        "🔸 **Breakout Classes (Morning):**\n"
        "  • 09:00 - 10:00 am | English 1 - Dr. Sintayehu (G1 - 003)\n"
        "  • 09:00 - 10:00 am | Calculus 1 - Dr. Zebene (G6 - 002)\n"
        "  • 10:15 - 11:15 am | English 1 - Dr. Sintayehu (G3 - 003)\n"
        "  • 10:15 - 11:15 am | Calculus 1 - Dr. Zebene (G5 - 002)\n\n"
        "🔸 **Main Classes (Afternoon):**\n"
        "  • 2:00 - 3:30 pm | Main Class"
    ),
    4: (
        "📚 **FRIDAY SCHEDULE**\n\n"
        "🔸 **Main Classes (Afternoon):**\n"
        "  • 3:45 - 5:00 pm | Calculus 1 - Prof. Abdulkadir Hassen"
    ),
    5: "🎉 **SATURDAY SCHEDULE**\n\nNo classes today! Enjoy your weekend.",
    6: "🎉 **SUNDAY SCHEDULE**\n\nNo classes today! Enjoy your weekend."
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
    
    weekday = datetime.now().weekday()
    schedule_message = DAILY_SCHEDULE.get(weekday, "No schedule found.")
    
    response_text = (
        "👋 **Welcome!** You are successfully subscribed to daily schedule reminders for **7:00 AM**.\n\n"
        "Here is what's on your agenda right now:\n\n"
        f"{schedule_message}"
    )
    
    await update.message.reply_text(response_text, parse_mode="Markdown")

async def send_schedule_to_all(bot: Bot):
    weekday = datetime.now().weekday()
    message = DAILY_SCHEDULE.get(weekday, "No schedule found.")
    
    for chat_id in subscribers:
        try:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
            logging.info(f"Schedule sent to {chat_id}")
        except Exception as e:
            logging.error(f"Failed to send to {chat_id}: {e}")

async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand("start", "Start bot & view today's schedule")
    ]
    await bot.set_my_commands(commands)

async def run_telegram_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))

    await set_bot_commands(app.bot)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_schedule_to_all, 'cron', hour=7, minute=0, args=[app.bot])
    scheduler.start()

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    logging.info("Telegram bot polling is active...")
    while True:
        await asyncio.sleep(3600)

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is alive and running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.start()
    asyncio.run(run_telegram_bot())
