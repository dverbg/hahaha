import asyncio

async def create_invoice(amount, user_id):
    # В реальном боте здесь интеграция с CryptoBot API или TG Stars
    invoice_id = f"INV{user_id}{int(asyncio.get_event_loop().time())}"
    url = f"https://cryptobot.fakepay/{invoice_id}"  # пример ссылки
    return url, invoice_id
