import time

async def create_invoice(amount, user_id):
    """
    Создаёт "инвойс" для оплаты (пример для CryptoBot / TG Stars)
    Возвращает: ссылка на оплату и ID инвойса
    """
    invoice_id = f"INV{user_id}{int(time.time())}"
    url = f"https://cryptobot.fakepay/{invoice_id}"  # пример ссылки
    return url, invoice_id
