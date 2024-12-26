import asyncpg
import config
import base64


async def create_table_admin(configfile):
    # Execute a statement to create a new table
    conn = await asyncpg.connect(
        user=base64.b64decode(configfile["database"]["username"]).decode("utf-8"),
        password=base64.b64decode(configfile["database"]["password"]).decode("utf-8"),
        database=base64.b64decode(configfile["database"]["name"]).decode("utf-8"),
        host=configfile["database"]["host"],
        port=configfile["database"]["port"]
    )
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS admins(
            id serial PRIMARY KEY,
            fullname varchar(150),
            email varchar(150) UNIQUE,
            access_provider_email varchar(150),
            whatsapp_number varchar(20) default Null,
            telegram_number varchar(30) default Null,
            country varchar(150) default Null,
            password varchar(150),
            user_type varchar(150),
            first_login TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    await conn.close()

