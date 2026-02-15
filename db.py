import aiomysql
import config

async def connect():
    return await aiomysql.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASS,
        db=config.DB_NAME
    )

async def add_user(id):
    db=await connect()
    async with db.cursor() as c:
        await c.execute("INSERT IGNORE INTO users(id) VALUES(%s)",(id,))
        await db.commit()

async def set_lang(id,l):
    db=await connect()
    async with db.cursor() as c:
        await c.execute("UPDATE users SET language=%s WHERE id=%s",(l,id))
        await db.commit()

async def register_user(id,login,password,uid):
    db=await connect()
    async with db.cursor() as c:
        await c.execute("UPDATE users SET login=%s,password=%s,uid=%s WHERE id=%s",(login,password,uid,id))
        await db.commit()

async def login_user(id,login,password):
    db=await connect()
    async with db.cursor() as c:
        await c.execute("SELECT id FROM users WHERE login=%s AND password=%s",(login,password))
        return await c.fetchone()

async def get_uid(id):
    db=await connect()
    async with db.cursor() as c:
        await c.execute("SELECT uid FROM users WHERE id=%s",(id,))
        r=await c.fetchone()
        return r[0]

async def get_keys(id):
    db=await connect()
    async with db.cursor() as c:
        await c.execute("SELECT license_key,display_name FROM licenses WHERE owner_id=%s",(id,))
        return await c.fetchall()

async def save_payment(invoice,user):
    db=await connect()
    async with db.cursor() as c:
        await c.execute("INSERT INTO payments(invoice_id,user_id) VALUES(%s,%s)",(invoice,user))
        await db.commit()
