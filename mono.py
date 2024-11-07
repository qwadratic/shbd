from requests import post
from config import read_config

config = read_config()
MONOBANK_API_TOKEN = config['mono']['api_token']
WEBHOOK_URL = config['mono']['webhook_url']
AMOUNT = int(config['mono']['amount'])


def generate_payment_url(user_id: int) -> str:
    url = "https://api.monobank.ua/api/merchant/invoice/create"
    data = {
        "amount": AMOUNT * 100,
        "merchantPaymInfo": {
            "destination": "За iнформацiйнi послуги",
            "comment": f"{user_id}",
            "reference": f"{user_id}"
        },
        "webHookUrl": WEBHOOK_URL
    }
    r = post(url, json=data, headers={
        "X-Token": MONOBANK_API_TOKEN
    })
    return r.json()['pageUrl']
