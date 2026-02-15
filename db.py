import os
import aiomysql

pool = None

async def init_db():
    global pool
    pool = await aiomysql.create_pool(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        autocommit=True
    )

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Таблица пользователей
            await cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                lang VARCHAR(5) DEFAULT 'ru',
                login VARCHAR(255),
                password_hash VARCHAR(255),
                uid VARCHAR(50)
            )
            """)
            # Таблица ключей (переименована в user_keys)
            await cur.execute("""
            CREATE TABLE IF NOT EXISTS user_keys (
                key_id VARCHAR(255) PRIMARY KEY,
                display_name VARCHAR(255),
                user_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            # Таблица платежей
            await cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                invoice_id VARCHAR(255) PRIMARY KEY,
                user_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

# ===== Функции для bot.py =====
async def add_user(user_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT IGNORE INTO users (user_id) VALUES (%s)", (user_id,)
            )

async def set_lang(user_id, lang):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE users SET lang=%s WHERE user_id=%s", (lang, user_id)
            )

async def register_user(user_id, login, password_hash, uid):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE users SET login=%s, password_hash=%s, uid=%s WHERE user_id=%s",
                (login, password_hash, uid, user_id)
            )

async def login_user(user_id, login, password_hash):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT * FROM users WHERE user_id=%s AND login=%s AND password_hash=%s",
                (user_id, login, password_hash)
            )
            row = await cur.fetchone()
            return bool(row)

async def get_uid(user_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT uid FROM users WHERE user_id=%s", (user_id,))
            row = await cur.fetchone()
            return row[0] if row else "Нет UID"

async def get_keys(user_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT key_id, display_name FROM user_keys WHERE user_id=%s", (user_id,)
            )
            rows = await cur.fetchall()
            return rows or []

async def save_key(key_id, display_name, user_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT IGNORE INTO user_keys (key_id, display_name, user_id) VALUES (%s,%s,%s)",
                (key_id, display_name, user_id)
            )

async def save_payment(invoice_id, user_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT IGNORE INTO payments (invoice_id, user_id) VALUES (%s, %s)",
                (invoice_id, user_id)
            )
