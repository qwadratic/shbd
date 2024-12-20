import asyncio
from datetime import datetime, timedelta, timezone
from config import read_config
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from models import get_async_session, get_users_without_payment
from mono import generate_payment_url
from apscheduler.schedulers.asyncio import AsyncIOScheduler

config = read_config()

async def notify_users():
    pyro_client = Client(
        "notification_bot",
        api_id=config['telegram']['api_id'],
        api_hash=config['telegram']['api_hash'],
        bot_token=config['telegram']['bot_token'],
    )
    await pyro_client.start()
    users = (await get_users_without_payment()).all()
    print(f"[{datetime.now(timezone.utc)}] Found {len(users)} users without payment")

    for user in users:
        u = user[0]
        if not u.last_notified or (u.last_notified + timedelta(days=5)).astimezone(timezone.utc) <= datetime.now(timezone.utc):
            try:
                await pyro_client.send_message(
                    u.user_id, 
                    "Ви не сплатили за доступ до чату. Будь ласка, сплатіть зараз. Якщо вам здається, що нагадування прийшло помилково, будь ласка, зверніться до @qwadratic.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            "Оплатити", 
                            url=generate_payment_url(u.user_id))
                        ]])
                    )
            except Exception as e:
                print(f"[{datetime.now(timezone.utc)}] Error sending message to user {u.user_id} {u.username} {u.display_name}: {e}")
            
            async with await get_async_session() as session:
                u.last_notified = datetime.now(timezone.utc)
                session.add(u)
                await session.commit()
            
            print(f"[{datetime.now(timezone.utc)}] Notified user {u.user_id} {u.username} {u.display_name}")

    await pyro_client.stop()

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(notify_users, 'interval', days=1, next_run_time=datetime.now(timezone.utc) + timedelta(seconds=1))
    scheduler.start()
    while True:
        await asyncio.sleep(1000)


if __name__ == "__main__":
    asyncio.run(main())
