import asyncio
import hashlib
import time
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db import init_db, add_user, set_lang, register_user, login_user, get_uid, get_keys, save_payment
from payments import create_invoice
from config import BOT_TOKEN

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# ===== Папка с картинками =====
IMG_DIR = os.path.join(os.path.dirname(__file__), "images")

# ===== АНТИФЛУД =====
cooldowns = {}
def antiflood(uid):
    now = time.time()
    if uid in cooldowns and now - cooldowns[uid] < 1.5:
        return True
    cooldowns[uid] = now
    return False

# ===== Inline клавиатуры =====
PLANS = {
    "7": {"days": 7, "price": 1},
    "30": {"days": 30, "price": 3},
    "90": {"days": 90, "price": 7}
}

def get_main_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
        InlineKeyboardButton(text="🗝 Мои ключи", callback_data="my_keys")
    )
    builder.row(
        InlineKeyboardButton(text="💳 Купить ключ", callback_data="buy_key"),
        InlineKeyboardButton(text="🚪 Выйти", callback_data="logout")
    )
    return builder.as_markup()

def get_payment_method_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 CryptoBot", callback_data="pay_cryptobot"),
        InlineKeyboardButton(text="⭐ Telegram Stars", callback_data="pay_stars")
    )
    return builder.as_markup()

def get_plans_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="7 дней — 1 USDT 💰", callback_data="plan_7"),
        InlineKeyboardButton(text="30 дней — 3 USDT 💰", callback_data="plan_30")
    )
    builder.row(
        InlineKeyboardButton(text="90 дней — 7 USDT 💰", callback_data="plan_90")
    )
    return builder.as_markup()

# ===== Функции отправки сообщений с картинками =====
async def send_authorization(user_id):
    with open(os.path.join(IMG_DIR, "authorization.png"), "rb") as photo:
        await bot.send_photo(
            user_id, photo,
            caption="**🔑 Авторизация / Регистрация**\nВведите _логин_ и _пароль_ через пробел",
            parse_mode="Markdown"
        )

async def send_main_menu(user_id):
    with open(os.path.join(IMG_DIR, "mainmenu.png"), "rb") as photo:
        await bot.send_photo(
            user_id, photo,
            caption="**🏠 Главное меню**\nВыберите действие:",
            parse_mode="Markdown",
            reply_markup=get_main_menu_kb()
        )

async def send_keys(user_id, keys_list):
    builder = InlineKeyboardBuilder()
    for k in keys_list:
        builder.add(InlineKeyboardButton(text=k, callback_data=f"key_{k}"))
    with open(os.path.join(IMG_DIR, "keys.png"), "rb") as photo:
        await bot.send_photo(
            user_id, photo,
            caption="**🗝 Ваши ключи**",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )

async def send_profile(user_id, uid):
    with open(os.path.join(IMG_DIR, "profile.png"), "rb") as photo:
        await bot.send_photo(
            user_id, photo,
            caption=f"**👤 Профиль**\nUID: `{uid}`",
            parse_mode="Markdown"
        )

# ===== ХЭНДЛЕРЫ =====
@dp.message(Command("start"))
async def start_cmd(msg: types.Message):
    await add_user(msg.from_user.id)
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Русский", callback_data="lang_ru"),
        InlineKeyboardButton(text="English", callback_data="lang_en")
    )
    await msg.answer("Выбери язык / Choose language", reply_markup=builder.as_markup())

@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def lang_choice(call: types.CallbackQuery):
    lang = call.data.split("_")[1]
    await set_lang(call.from_user.id, lang)
    await send_authorization(call.from_user.id)
    await call.answer()

@dp.callback_query(lambda c: c.data == "profile")
async def menu_profile(call: types.CallbackQuery):
    uid = await get_uid(call.from_user.id)
    await send_profile(call.from_user.id, uid)
    await call.answer()

@dp.callback_query(lambda c: c.data == "my_keys")
async def menu_keys(call: types.CallbackQuery):
    rows = await get_keys(call.from_user.id)
    keys_text = [f"{r[1] or 'Без имени'} — {r[0]}" for r in rows] if rows else ["Нет ключей"]
    await send_keys(call.from_user.id, keys_text)
    await call.answer()

@dp.callback_query(lambda c: c.data == "buy_key")
async def menu_buy_key(call: types.CallbackQuery):
    await call.message.edit_text(
        text="Выберите способ оплаты:",
        reply_markup=get_payment_method_kb()
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("pay_"))
async def choose_payment_method(call: types.CallbackQuery):
    method = call.data.split("_")[1]
    if method == "cryptobot":
        await call.message.edit_text(
            text="Выберите тариф для CryptoBot:",
            reply_markup=get_plans_kb()
        )
    else:
        await call.message.edit_text(
            text="Выберите тариф для Telegram Stars:",
            reply_markup=get_plans_kb()
        )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("plan_"))
async def choose_plan(call: types.CallbackQuery):
    pid = call.data.split("_")[1]
    plan = PLANS[pid]
    # Для CryptoBot создаем инвойс
    url, invoice = await create_invoice(plan["price"], call.from_user.id)
    await save_payment(invoice, call.from_user.id)
    await call.message.edit_text(
        text=f"💰 Оплатите {plan['price']} USDT:\n{url}"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "logout")
async def menu_logout(call: types.CallbackQuery):
    await call.message.edit_text("Вы вышли. /start")
    await call.answer()

# ===== Логин / регистрация =====
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

# ===== Старт бота =====
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
