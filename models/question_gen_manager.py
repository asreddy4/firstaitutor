import asyncpg
import config
import base64

async def create_table_question_gen_manager(configfile):
    # Execute a statement to create a new table
    conn = await asyncpg.connect(
        user=base64.b64decode(configfile["database"]["username"]).decode("utf-8"),
        password=base64.b64decode(configfile["database"]["password"]).decode("utf-8"),
        database=base64.b64decode(configfile["database"]["name"]).decode("utf-8"),
        host=configfile["database"]["host"],
        port=configfile["database"]["port"]
    )
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS question_gen_manager(
            id serial PRIMARY KEY,
            qt_id varchar(150),
            qt_title varchar(150),
            qt_format varchar(150),
            q_spec TEXT default Null,
            q_variation varchar(150),
            q_assigned_to varchar(150) default Null,
            q_creator_approved BOOLEAN default FALSE,
            q_num_db int default 0,
            q_unused_db int default 0,
            q_manager_name varchar(150),    
            q_manager_approved BOOLEAN default FALSE,
            q_locked BOOLEAN default FALSE,
            q_json_file_exist BOOLEAN default FALSE,
            q_html_file_exist BOOLEAN default FALSE,
            q_html_file_link varchar(200) default Null,
            set_edit_spec JSONB default Null,
            html_generated TEXT default Null,
            q_num_add_to_db int default 0,
            q_logs TEXT default Null,
            comment TEXT default Null,
            time_created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            time_last_edited TIMESTAMP,
            last_created_user_id int
            )
    ''')
    await conn.close()

