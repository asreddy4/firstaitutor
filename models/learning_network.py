import asyncpg
import config
import base64

async def create_table_learning_network(configfile):
    # Execute a statement to create a new table
    conn = await asyncpg.connect(
        user=base64.b64decode(configfile["database"]["username"]).decode("utf-8"),
        password=base64.b64decode(configfile["database"]["password"]).decode("utf-8"),
        database=base64.b64decode(configfile["database"]["name"]).decode("utf-8"),
        host=configfile["database"]["host"],
        port=configfile["database"]["port"]
    )
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS learning_network(
            id serial PRIMARY KEY,
            ln_id varchar(150),
            title varchar(150),
            subject_id varchar(150),
            parent_nodes varchar(150),
            max_order int,
            back_learning_level int,
            is_subject_head_node BOOLEAN,
            is_keynode BOOLEAN,
            support_url varchar(150),
            time_created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            time_last_edited TIMESTAMP,
            last_created_user_id int
            )
    ''')
    await conn.close()

