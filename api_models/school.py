import asyncpg
import config
import sys
import base64



async def create_table_school(configfile):
    # Execute a statement to create a new table
    conn = await asyncpg.connect(
        user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
        database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
        host=str(configfile["database"]["host"]),
        port=str(configfile["database"]["port"])
    )
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS school(
            id serial PRIMARY KEY,
            name varchar(150),
            country_code varchar(150) NOT NULL,
            county_state varchar(150) default Null,
            identification_code varchar(150) default Null
        )
    ''')
    await conn.close()

