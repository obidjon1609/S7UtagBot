import asyncio
from aiogram import Bot
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def delete_webhook():
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook deleted successfully!")
        await bot.session.close()
    except Exception as e:
        print(f"❌ Error deleting webhook: {e}")

if __name__ == "__main__":
    asyncio.run(delete_webhook())
