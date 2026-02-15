import asyncio
import hashlib
import time
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from db import connect, init_db, add_user, set_lang, register_user, login_user, get_uid, get_keys, save_payment
from payments import create_invoice

# ================== ПЕРЕМЕННЫЕ ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# ================== АНТИФЛУД ==================
cooldowns = {}
def antiflood(uid):
    now = time.time()
    if uid in cooldowns and now - cooldowns[uid] < 1.5:
        return True
    cooldowns[uid] = now
    return False

# ================== КНОПКИ ==================
lang_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Русский")],[KeyboardButton(text="English")]],
    resize_keyboard=True
)

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Профиль"), KeyboardButton(text="Мои ключи")],
        [KeyboardButton(text="Купить ключ"), KeyboardButton(text="Выйти")]
    ],
    resize_keyboard=True
)

PLANS = {
    "7": {"days": 7, "price": 1},
    "30": {"days": 30, "price": 3},
    "90": {"days": 90, "price": 7}
}

plans_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="7 дней — 1 USDT", callback_data="buy_7")],
    [InlineKeyboardButton(text="30 дней — 3 USDT", callback_data="buy_30")],
    [InlineKeyboardButton(text="90 дней — 7 USDT", callback_data="buy_90")]
])

# ================== ХЭНДЛЕРЫ ==================
@dp.message(Command("start"))
async def start_cmd(msg: types.Message):
    await add_user(msg.from_user.id)
    await msg.answer("Выбери язык", reply_markup=lang_kb)

@dp.message(lambda m: m.text in ["Русский", "English"])
async def lang_choice(msg: types.Message):
    await set_lang(msg.from_user.id, msg.text)
    await msg.answer("Введи логин и пароль через пробел")

@dp.message(lambda m: m.text == "Купить ключ")
async def buy_key(msg: types.Message):
    await msg.answer("Выбери тариф", reply_markup=plans_kb)

@dp.callback_query(lambda c: c.data.startswith("buy_"))
async def buy_plan(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    plan = PLANS[pid]

    url, invoice = await create_invoice(plan["price"], call.from_user.id)
    await save_payment(invoice, call.from_user.id)

    await call.message.answer(f"💳 Оплати {plan['price']} USDT:\n{url}")

@dp.message(lambda m: m.text == "Профиль")
async def profile(msg: types.Message):
    uid = await get_uid(msg.from_user.id)
    await msg.answer(f"UID: {uid}")

@dp.message(lambda m: m.text == "Мои ключи")
async def my_keys(msg: types.Message):
    rows = await get_keys(msg.from_user.id)
    if not rows:
        return await msg.answer("Нет ключей")
    text = "\n".join([f"{r[1] or 'Без имени'} — {r[0]}" for r in rows])
    await msg.answer(text)

@dp.message(lambda m: m.text == "Выйти")
async def logout(msg: types.Message):
    await msg.answer("Вы вышли. /start")

@dp.message()
async def login_handler(msg: types.Message):
    if antiflood(msg.from_user.id):
        return
    parts = msg.text.strip().split()
    if len(parts) != 2:
        return
    login, password = parts
    h = hashlib.sha256(password.encode()).hexdigest()
    ok = await login_user(msg.from_user.id, login, h)
    if ok:
        await msg.answer("🎉 Вход выполнен", reply_markup=main_kb)
    else:
        uid = f"UID{msg.from_user.id}"
        await register_user(msg.from_user.id, login, h, uid)
        await msg.answer("🎉 Аккаунт создан", reply_markup=main_kb)

# ================== СТАРТ БОТА ==================
async def main():
    await init_db()  # Автоинициализация таблиц
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
