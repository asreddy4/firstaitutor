import os
from typing import final
import base64
import asyncpg
import sys
import asyncio
# import config


async def create_table_qualification(configfile):
    # Execute a statement to create a new table
    try:
        # Connect to PostgreSQL database
        conn = await asyncpg.connect(
            user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
            password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
            database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
            host = str(configfile["database"]["host"]),
            port = str(configfile["database"]["port"])
        )

        # Create the table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS qualification(
                id serial PRIMARY KEY,
                q_id varchar(150),
                title varchar(150),
                country_code varchar(150),
                subject_id int,
                age int,
                study_level varchar(150),
                var varchar(150),
                org varchar(150),
                grade varchar(150),
                modules varchar(150) default Null,
                time_created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                time_last_edited TIMESTAMP,
                last_created_user_id int,
                CONSTRAINT fk_subject FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE RESTRICT
                )
        ''')
    except Exception as e:
        print(f"Error while creating table: {e}")
    finally:
        await conn.close()
# asyncio.run(create_table_qualification())
