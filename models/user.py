import asyncpg
import config
import base64


async def create_table_user(configfile):
    # Execute a statement to create a new table
    conn = await asyncpg.connect(
        user=base64.b64decode(configfile["database"]["username"]).decode("utf-8"),
        password=base64.b64decode(configfile["database"]["password"]).decode("utf-8"),
        database=base64.b64decode(configfile["database"]["name"]).decode("utf-8"),
        host=configfile["database"]["host"],
        port=configfile["database"]["port"]
    )
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id serial PRIMARY KEY,
            student_id varchar(150) default Null,
            email varchar(150) UNIQUE,
            first_name varchar(150) default Null,
            last_name varchar(150) default Null,
            phone varchar(20) ,
            is_admin BOOLEAN default FALSE ,
            is_active BOOLEAN default TRUE,
            date_of_birth date,
            first_login TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            country_code varchar(150),
            city_code varchar(150),
            school_id int,
            qualification_id int default Null,
            qualification_target_grade varchar(150) default Null,
            user_type int ,
            password varchar(150)
        )
    ''')
    await conn.close()

