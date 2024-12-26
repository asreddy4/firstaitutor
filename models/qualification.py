import asyncpg
import config
import base64

async def create_table_qualification(configfile):
    # Execute a statement to create a new table
    conn = await asyncpg.connect(user= base64.b64decode(configfile["database"]["username"]).decode("utf-8"),
        password= base64.b64decode(configfile["database"]["password"]).decode("utf-8"),
        database= base64.b64decode(configfile["database"]["name"]).decode("utf-8"),
        host=configfile["database"]["host"],
        port=configfile["database"]["port"])
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS qualification(
            id serial PRIMARY KEY,
            qual_id varchar(150),
            title varchar(150),
            country_code varchar(150),
            subject_id varchar(150),
            age int,
            study_level JSONB default Null,
            var JSONB default Null,
            org JSONB default Null,
            grade JSONB default Null,
            modules JSONB default Null,
            time_created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            time_last_edited TIMESTAMP,
            last_created_user_id int
            )
    ''')
    await conn.close()

