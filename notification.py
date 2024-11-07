from datetime import datetime, timedelta, timezone
from config import read_config
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from models import get_async_session, get_users_without_payment
from mono import generate_payment_url
from apscheduler.schedulers.asyncio import AsyncIOScheduler

config = read_config()
pyro_client = Client(
    "notification_bot",
    api_id=config['telegram']['api_id'],
    api_hash=config['telegram']['api_hash'],
    bot_token=config['telegram']['bot_token']
)

async def notify_users():
    users = await get_users_without_payment()
    for user in users:
        u = user[0]
        if not u.last_notified or u.last_notified + timedelta(days=5) >= datetime.now(timezone.utc):
            await pyro_client.send_message(
                u.id, 
                "Ви не сплатили за останню оплату. Будь ласка, сплатіть зараз.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        "Оплатити", 
                        url=generate_payment_url(u.id))
                    ]])
                )
            async with await get_async_session() as session:
                u.last_notified = datetime.now(timezone.utc)
                await session.commit()

if __name__ == "__main__":
    scheduler = AsyncIOScheduler()
    scheduler.add_job(notify_users, 'interval', days=1)
    scheduler.start()
