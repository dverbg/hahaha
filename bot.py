import asyncio
import hashlib
import time
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from db import init_db, add_user, set_lang, register_user, login_user, get_uid, get_keys, save_payment
from payments import create_invoice
from config import BOT_TOKEN

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# ===== АНТИФЛУД =====
cooldowns = {}
def antiflood(uid):
    now = time.time()
    if uid in cooldowns and now - cooldowns[uid] < 1.5:
        return True
    cooldowns[uid] = now
    return False

# ===== КНОПКИ =====
lang_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton("Русский")],[KeyboardButton("English")]],
    resize_keyboard=True
)

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("👤 Профиль"), KeyboardButton("🗝 Мои ключи")],
        [KeyboardButton("💳 Купить ключ"), KeyboardButton("🚪 Выйти")]
    ],
    resize_keyboard=True
)

PLANS = {
    "7": {"days": 7, "price": 1},
    "30": {"days": 30, "price": 3},
    "90": {"days": 90, "price": 7}
}

plans_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton("7 дней — 1 USDT 💰", callback_data="buy_7")],
    [InlineKeyboardButton("30 дней — 3 USDT 💰", callback_data="buy_30")],
    [InlineKeyboardButton("90 дней — 7 USDT 💰", callback_data="buy_90")]
])

# ===== ФУНКЦИИ ОТПРАВКИ =====
async def send_authorization(user_id):
    with open("images/authorization.png","rb") as photo:
        await bot.send_photo(user_id, photo, caption="**🔑 Авторизация / Регистрация**\nВведите _логин_ и _пароль_ через пробел", parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True))

async def send_main_menu(user_id):
    with open("images/mainmenu.png","rb") as photo:
        await bot.send_photo(user_id, photo, caption="**🏠 Главное меню**\nВыберите действие:", parse_mode="Markdown", reply_markup=main_kb)

async def send_keys(user_id, keys_list):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for k in keys_list:
        kb.add(KeyboardButton(k))
    with open("images/keys.png","rb") as photo:
        await bot.send_photo(user_id, photo, caption="**🗝 Ваши ключи**", parse_mode="Markdown", reply_markup=kb)

async def send_profile(user_id, uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🚪 Выйти"))
    with open("images/profile.png","rb") as photo:
        await bot.send_photo(user_id, photo, caption=f"**👤 Профиль**\nUID: `{uid}`", parse_mode="Markdown", reply_markup=kb)

# ===== ХЭНДЛЕРЫ =====
@dp.message(Command("start"))
async def start_cmd(msg: types.Message):
    await add_user(msg.from_user.id)
    await msg.answer("Выбери язык / Choose language", reply_markup=lang_kb)

@dp.message(lambda m: m.text in ["Русский","English"])
async def lang_choice(msg: types.Message):
    await set_lang(msg.from_user.id, msg.text)
    await send_authorization(msg.from_user.id)

@dp.message(lambda m: m.text == "💳 Купить ключ")
async def buy_key(msg: types.Message):
    with open("images/keys.png","rb") as photo:
        await bot.send_photo(msg.from_user.id, photo, caption="**💳 Выберите тариф**", parse_mode="Markdown", reply_markup=plans_kb)

@dp.callback_query(lambda c: c.data.startswith("buy_"))
async def buy_plan(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    plan = PLANS[pid]
    url, invoice = await create_invoice(plan["price"], call.from_user.id)
    await save_payment(invoice, call.from_user.id)
    await call.message.answer(f"💰 Оплатите {plan['price']} USDT:\n{url}")

@dp.message(lambda m: m.text == "👤 Профиль")
async def profile(msg: types.Message):
    uid = await get_uid(msg.from_user.id)
    await send_profile(msg.from_user.id, uid)

@dp.message(lambda m: m.text == "🗝 Мои ключи")
async def my_keys(msg: types.Message):
    rows = await get_keys(msg.from_user.id)
    keys_text = [f"{r[1] or 'Без имени'} — {r[0]}" for r in rows] if rows else ["Нет ключей"]
    await send_keys(msg.from_user.id, keys_text)

@dp.message(lambda m: m.text == "🚪 Выйти")
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
        await send_main_menu(msg.from_user.id)
    else:
        uid = f"UID{msg.from_user.id}"
        await register_user(msg.from_user.id, login, h, uid)
        await send_main_menu(msg.from_user.id)

# ===== СТАРТ БОТА =====
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
