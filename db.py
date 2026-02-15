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
            await cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                lang VARCHAR(5) DEFAULT 'ru',
                login VARCHAR(255),
                password_hash VARCHAR(255),
                uid VARCHAR(50)
            )
            """)
            await cur.execute("""
            CREATE TABLE IF NOT EXISTS keys (
                key VARCHAR(255) PRIMARY KEY,
                display_name VARCHAR(255),
                user_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            await cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                invoice_id VARCHAR(255) PRIMARY KEY,
                user_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

async def get_connection():
    return pool

# остальные функции add_user, set_lang, register_user, login_user, get_uid, get_keys, save_payment
# такие же как я присылал ранее
