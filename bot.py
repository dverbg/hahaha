import hashlib
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import config
from db import *
from payments import create_invoice

bot = Bot(config.BOT_TOKEN)
dp = Dispatcher()

cooldowns = {}

def antiflood(uid):
    now=time.time()
    if uid in cooldowns and now-cooldowns[uid]<1.5:
        return True
    cooldowns[uid]=now
    return False


lang_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Русский")],[KeyboardButton(text="English")]],
    resize_keyboard=True
)

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Профиль"),KeyboardButton(text="Мои ключи")],
        [KeyboardButton(text="Купить ключ"),KeyboardButton(text="Выйти")]
    ],resize_keyboard=True
)

PLANS={
"7":{"days":7,"price":1},
"30":{"days":30,"price":3},
"90":{"days":90,"price":7}
}

plans_kb = InlineKeyboardMarkup(inline_keyboard=[
[InlineKeyboardButton(text="7 дней — 1 USDT",callback_data="buy_7")],
[InlineKeyboardButton(text="30 дней — 3 USDT",callback_data="buy_30")],
[InlineKeyboardButton(text="90 дней — 7 USDT",callback_data="buy_90")]
])


@dp.message(Command("start"))
async def start(m:types.Message):
    await add_user(m.from_user.id)
    await m.answer("Выбери язык",reply_markup=lang_kb)


@dp.message(F.text.in_(["Русский","English"]))
async def lang(m:types.Message):
    await set_lang(m.from_user.id,m.text)
    await m.answer("Введи логин пароль через пробел")


@dp.message(F.text=="Купить ключ")
async def buy(m:types.Message):
    await m.answer("Выбери тариф",reply_markup=plans_kb)


@dp.callback_query(F.data.startswith("buy_"))
async def buyplan(call):
    pid=call.data.split("_")[1]
    plan=PLANS[pid]

    url,invoice=await create_invoice(plan["price"],call.from_user.id)
    await save_payment(invoice,call.from_user.id)

    await call.message.answer(f"Оплати {plan['price']} USDT:\n{url}")


@dp.message(F.text=="Профиль")
async def profile(m:types.Message):
    uid=await get_uid(m.from_user.id)
    await m.answer(f"UID: {uid}")


@dp.message(F.text=="Мои ключи")
async def keys(m:types.Message):
    rows=await get_keys(m.from_user.id)
    if not rows:
        return await m.answer("Нет ключей")
    text="\n".join([f"{i[1] or 'Без имени'} — {i[0]}" for i in rows])
    await m.answer(text)


@dp.message(F.text=="Выйти")
async def exit(m:types.Message):
    await m.answer("Вы вышли /start")


@dp.message()
async def login(m:types.Message):
    if antiflood(m.from_user.id): return
    t=m.text.split()
    if len(t)!=2:return
    login,password=t

    h=hashlib.sha256(password.encode()).hexdigest()
    ok=await login_user(m.from_user.id,login,h)

    if ok:
        await m.answer("🎉 Вход выполнен",reply_markup=main_kb)
    else:
        uid=f"UID{m.from_user.id}"
        await register_user(m.from_user.id,login,h,uid)
        await m.answer("🎉 Аккаунт создан",reply_markup=main_kb)


async def main():
    await dp.start_polling(bot)

if __name__=="__main__":
    import asyncio
    asyncio.run(main())
