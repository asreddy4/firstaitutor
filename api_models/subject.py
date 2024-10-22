import asyncpg
import config
import sys
import os
import base64

async def create_table_subject(configfile):
    # Execute a statement to create a new table
    conn = await asyncpg.connect(
        user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
        database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
        host=str(configfile["database"]["host"]),
        port=str(configfile["database"]["port"])
    )
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS subject(
            id serial PRIMARY KEY,
            s_id varchar(150),
            name varchar(150)
        )
    ''')
    await conn.close()

