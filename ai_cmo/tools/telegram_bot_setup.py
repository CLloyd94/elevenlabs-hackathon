import logging
from py.msg.telegram_message_sender import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import asyncio
from dotenv import load_dotenv
import os

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Start the bot
async def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    logger.info(f"/start command received from {user.first_name} ({user.id})")

# Error handler
async def error_handler(update: Update, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    logger.warning(f'Update "{update}" caused error "{context.error}"')

async def log_update(update: Update, context: CallbackContext) -> None:
    """Log all incoming updates."""
    logger.info(f"Received update: {update}")

async def trigger_function():
    print("Triggered function executed!")
    logger.info("trigger_function was invoked externally.")

def console_listener(app: Application):
    while True:
        command = input("Enter command (type 'trigger' to run trigger_function): ").strip()
        if command.lower() == "trigger":
            # Schedule the coroutine in the bot's event loop
            future = asyncio.run_coroutine_threadsafe(trigger_function(), app.loop)
            try:
                future.result(timeout=10)  # Wait for the result if needed
            except Exception as e:
                print("Error triggering function:", e)

def main() -> None:
    """Start the bot."""
    load_dotenv()

    token = os.getenv("BOT_TOKEN")
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    
    # Log all updates
    app.add_handler(MessageHandler(filters.ALL, log_update))

    # Log errors
    app.add_error_handler(error_handler)

    # Start the bot
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()