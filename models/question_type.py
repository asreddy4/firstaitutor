import asyncpg
import config
import base64

async def create_table_question_type(configfile):
    # Execute a statement to create a new table
    conn = await asyncpg.connect(
        user=base64.b64decode(configfile["database"]["username"]).decode("utf-8"),
        password=base64.b64decode(configfile["database"]["password"]).decode("utf-8"),
        database=base64.b64decode(configfile["database"]["name"]).decode("utf-8"),
        host=configfile["database"]["host"],
        port=configfile["database"]["port"]
    )
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS question_type(
            id serial PRIMARY KEY,
            qt_id varchar(150),
            title varchar(150),
            ln_id varchar(150),
            parent_nodes JSONB default Null,
            qual_dict JSONB,
            qt_age int,
            qt_format varchar(150),
            qt_order int,
            repeatable_pattern varchar(150),
            period_pattern varchar(150) default Null,
            time_created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            time_last_edited TIMESTAMP,
            last_created_user_id int,
            country_id JSONB,
            page_script TEXT default Null,
            is_non_calculator BOOLEAN default TRUE,
            min_time int,
            max_time int,
            end_time int,
            learning_content TEXT default Null
            )
    ''')
    await conn.close()

