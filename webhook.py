from pyrogram import Client
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from datetime import datetime, timedelta, timezone
import json
import uvicorn

from config import read_config
from models import User, get_async_session

config = read_config()
pyro_client = Client(
    "webhook_handler",
    api_id=config['telegram']['api_id'],
    api_hash=config['telegram']['api_hash'],
    bot_token=config['telegram']['bot_token']
)

fastapi_app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await pyro_client.start()
    yield
    await pyro_client.stop()

fastapi_app.router.lifespan_context = lifespan

@fastapi_app.post("/wh")
async def payment_webhook(request: Request):
    try:
        # Get the payment data from the webhook
        payload = await request.json()
        
        # Verify webhook signature (implement according to your payment provider)
        # verify_webhook_signature(request.headers, payload)
        
        # Extract payment details
        user_id = payload.get('reference')
        payment_status = payload.get('status')
        print(payload['reference'], payload['status'], payload.get('invoiceId'))
        print(json.dumps(payload, indent=2))
        if payment_status == 'success':
            await pyro_client.send_message(
                user_id, "Успішно оплачено! Наступна оплата: " + 
                (datetime.now(timezone.utc) + timedelta(days=30)).strftime('%Y-%m-%d')
            )
            async with await get_async_session() as session:
                user = await session.get(User, user_id)
                user.last_paid = datetime.now(timezone.utc)
                user.last_notified = datetime.now(timezone.utc)
                session.add(user)
                await session.commit()

        # if not all([user_id, amount, payment_status]):
        #     raise HTTPException(status_code=400, detail="Missing required payment information")
            
        # if payment_status == 'successful':
        #     conn = sqlite3.connect('users.db')
        #     c = conn.cursor()
            
        #     current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        #     next_payment = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
            
        #     c.execute('''UPDATE users 
        #                 SET last_paid = ?, next_payment = ?
        #                 WHERE user_id = ?''', (current_time, next_payment, user_id))
        #     conn.commit()
        #     conn.close()
            
        #     # You might want to notify the user via bot here
        #     # This would require setting up communication between FastAPI and your bot
            
        #     return {"status": "success", "message": "Payment processed successfully"}
        # else:
        #     raise HTTPException(status_code=400, detail="Payment not successful")
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000) 