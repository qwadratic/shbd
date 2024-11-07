from sqlalchemy import and_, or_, select
from models import User, get_async_session, init_db
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta, timezone
from config import read_config
from mono import generate_payment_url

config = read_config()


app = Client(
    "payment_bot",
    api_id=config['telegram']['api_id'],
    api_hash=config['telegram']['api_hash'],
    bot_token=config['telegram']['bot_token']
)

async def send_message(user_id: int, message: str):
    async with app:
        await app.send_message(user_id, message)

async def get_users_without_payment():
    async with await get_async_session() as session:
        return await session.execute(
            select(User).where(
                or_(
                    User.last_paid < datetime.now(timezone.utc) - timedelta(days=30), 
                    User.last_paid == None)))

async def get_users_with_payment():
    q = select(User).where(
            and_(
                User.last_paid != None,
                User.last_paid > datetime.now(timezone.utc) - timedelta(days=30)))
    async with await get_async_session() as session:
        return await session.execute(q)

@app.on_message(filters.command("unpaid") & filters.create(lambda _, __, m: m.from_user.id in config['telegram']['admin_ids']))
async def unpaid(client, message):
    users = await get_users_without_payment()
    await message.reply(f"Не сплатили:\n{'\n'.join([f'{user[0].display_name} (@{user[0].username})' for user in users])}")

@app.on_message(filters.command("paid"))
async def paid(client, message):
    users = await get_users_with_payment()
    await message.reply(f"Сплатили:\n{'\n'.join([f'{user[0].display_name} (@{user[0].username})' for user in users])}")

@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    async with await get_async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            user = User(
                user_id=user_id, 
                username=message.from_user.username,
                display_name=message.from_user.first_name or "" + " " + message.from_user.last_name or ""
            )
            session.add(user)
            await session.commit()

            payment_url = generate_payment_url(user_id)
            await message.reply(f"Ви успiшно зареєстрованi!")
            await message.reply(
                f"Натиснiть кнопку нижче для оплати", 
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        "Оплатити", 
                        url=payment_url)
                    ]])
                )
        else:
            await message.reply(f"Привiт, {user.display_name}!")
            if not user.last_paid or user.last_paid + timedelta(days=30) < datetime.now(timezone.utc):
                payment_url = generate_payment_url(user_id)
                await message.reply(
                    f"Ваша пiдписка закiнчилася. Натиснiть кнопку нижче для оплати",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            "Оплатити", 
                            url=payment_url)
                        ]])
                    )


if __name__ == "__main__":
    init_db()
    app.run()
