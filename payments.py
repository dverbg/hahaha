import aiohttp
import config

async def create_invoice(amount, user_id):
    async with aiohttp.ClientSession() as session:
        headers = {"Crypto-Pay-API-Token": config.CRYPTO_TOKEN}
        data = {
            "asset": "USDT",
            "amount": amount,
            "payload": str(user_id)
        }
        async with session.post("https://pay.crypt.bot/api/createInvoice", json=data, headers=headers) as r:
            res = await r.json()
            return res["result"]["pay_url"], res["result"]["invoice_id"]
