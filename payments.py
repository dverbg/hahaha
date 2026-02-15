import time

async def create_invoice(amount, user_id):
    invoice_id = f"INV{user_id}{int(time.time())}"
    url = f"https://cryptobot.fakepay/{invoice_id}"
    return url, invoice_id
