import asyncio
import base64
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import asyncpg
from fastapi import APIRouter, Request, Header, HTTPException, status, Request, Query
from pymongo import MongoClient
from pydantic import BaseModel, constr, Field

import json
import os
import yaml
from tomlkit import document
# from q_gen import question_generator
import sys
from pathlib import Path
import inspect
import ast
from copy import deepcopy

from utils.tools import find_user_id_by_token
from validations.question_generation import Question_gen, QuestionGeneration, Response
import subprocess

routers_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
firstaitutor_dir = os.path.dirname(routers_dir)
fait_backend_dir = os.path.dirname(firstaitutor_dir)
home_dir = os.path.dirname(fait_backend_dir)

sys.path.insert(0, f'{fait_backend_dir}/fait_python/gen_raw_questions')

configfile = {}
scriptDir = os.path.dirname(os.path.abspath(__file__))
config_filepath = str(os.path.dirname(scriptDir)+"/configfile.yml")

if os.path.exists(config_filepath):
    with open(config_filepath, 'rt') as configFile:
        try:
            configfile = yaml.safe_load(configFile.read())
        except Exception as e:
            print("Check the ConfigFile "+str(e))

scriptDir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
question_variations = scriptDir +'/fait_back_res/backend_data_options/question_variations.json'

def read_question_variations(file_path : str):
    with open(file_path, 'r') as file:
        return json.load(file)

router = APIRouter()

@router.get("/details", description="Fetch specific questions with qt_id from mongodb", summary="Get all questions", tags=["mongodb"])
async def get_details(name: str = Query(..., example="001a-001a-001a-001a-0001a", description="question_type id")):
    client = MongoClient(
        host=configfile["mongodb"]["host"],
        port=configfile["mongodb"]["port"],
        username=(base64.b64decode(configfile["mongodb"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["mongodb"]["password"])).decode("utf-8"),
    )
    db = client[name[:14]]
    collection = db[name]
    try:
        details_list = []
        for data in collection.find({}, {"_id": 0}):
            for question_id in data:
                for i in data[question_id]:
                    details_list.append(i)
        return {"details": details_list}
    except Exception as e:
        return str(e)

@router.post("/add/data", summary="Add json data to database", tags=["mongodb"])
async def add_data(question: Question_gen):
    client = MongoClient(
        host=configfile["mongodb"]["host"],
        port=configfile["mongodb"]["port"],
        username=(base64.b64decode(configfile["mongodb"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["mongodb"]["password"])).decode("utf-8"),
    )
    try:
        db = client[question.qt_id[:14]]
        # collection_name = question.qt_id
        collection = db[question.qt_id]
        document_name = question.qt_id + f"_{question.q_var_to_generate}"

        match_file = str(os.path.dirname(scriptDir)+"/utils/match.json")
        with open(match_file, "r") as file:
            data = json.load(file)
        collection.insert_one({f"{document_name}": data})
        return {
            "message" : f"Question ID {question.qt_id} Successfully added",
        }

        # p = question_generator(question.qt_id, question.q_numb_to_generate, question.q_var_to_generate, question.action_code, question.qt_format)
        # print("Here is the Error:", question_generator.stderr)
        #
        # if question.action_code == 1:
        #     output_dict = deepcopy(p.stdout.splitlines()[p.stdout.splitlines().index('fait_output')+1])
        # elif question.action_code == 0:
        #     output_dict = deepcopy(ast.literal_eval(p.stdout.splitlines()[p.stdout.splitlines().index('fait_output')+1]))
        #
        # print("output:", output_dict)
    except Exception as e:
        return str(e)


@router.post("/question/generate", summary="Generate Question", tags=["mongodb"])
async def generate_question(question_gen: QuestionGeneration, token: str = Header(...)):
    loop = asyncio.get_running_loop()
    user_id = await loop.run_in_executor(ThreadPoolExecutor(), find_user_id_by_token, token)
    if not user_id:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED, message="Invalid session ID")

    conn = await asyncpg.connect(
        user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
        database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
        host=str(configfile["database"]["host"]),
        port=str(configfile["database"]["port"])
    )
    query = "SELECT * FROM admins WHERE id = $1"
    existing_user = await conn.fetchrow(query, int(user_id))
    await conn.close()

    if existing_user['user_type'] not in {"admin", "content_manager", "super_admin", "question_creator"}:
        return Response(
            status_code=status.HTTP_403_FORBIDDEN,
            message="You do not have access to this section",
            data=None,
            detail=None
        )
    try:
        # p= subprocess.run([f"{fait_backend_dir}/fait_python/windowsenv/Scripts/python", f"{fait_backend_dir}/fait_python/gen_raw_questions/match.py", f"{qt_id}", f"{q_numb}", f"{is_test}"],
        # p= subprocess.run([f"{fait_backend_dir}/fait_python/ubuntuenv/bin/python", f"{fait_backend_dir}/fait_python/gen_raw_questions/match.py", f"{qt_id}", f"{q_numb_to_generate}", f"{q_var_to_generate}", f"{action_code}"],
        # p= subprocess.run([f"{fait_backend_dir}/fait_python/ubuntuenv/bin/python", f"{fait_backend_dir}/fait_python/gen_raw_questions/blank.py", f"{qt_id}", f"{q_numb_to_generate}", f"{q_var_to_generate}", f"{action_code}"],
        p = subprocess.run([f"{fait_backend_dir}/fait_python/ubuntuenv/bin/python", f"{fait_backend_dir}/fait_python/gen_raw_questions/{question_gen.qt_format}.py", f"{question_gen.qt_id}", f"{question_gen.q_numb_to_generate}", f"{question_gen.q_var_to_generate}", f"{question_gen.action_code}", f"{question_gen.current_q_num}"],
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           shell=False,
                           text=True
                           )
        if p.stderr:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="The request was unsuccessful",
                data={"error": p.stderr},
                detail=None
            )
            # print("Here is the Error:", p.stderr)

        conn = await asyncpg.connect(
            user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
            password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
            database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
            host=str(configfile["database"]["host"]),
            port=str(configfile["database"]["port"])
        )
        question_variations_json = read_question_variations(question_variations)
        variation = question_variations_json.get(str(question_gen.q_var_to_generate))
        if variation is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="The variation is not valid",
                data={"q_variations": list(question_variations_json.keys())},
                detail=None
            )

        existing_qts = await conn.fetchrow(
            'SELECT * FROM question_gen_manager WHERE qt_id = $1 and q_variation = $2 and q_manager_name = $3',
            question_gen.qt_id, variation, existing_user['fullname']
        )
        if existing_qts is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"The qt_id '{question_gen.qt_id}' with variation '{variation}' is not exists or this question not assigned to '{existing_user['fullname']}'.",
                data=None,
                detail=None
            )
        current_q_num = existing_qts['q_num_db']
        if question_gen.action_code == 1:
            output_dict = deepcopy(p.stdout.splitlines()[p.stdout.splitlines().index('fait_output') + 1])
            now = datetime.utcnow()
            query = """
                        UPDATE question_gen_manager
                        SET q_num_add_to_db = $1, q_num_db = $2, q_unused_db = $3, time_last_edited = $4, last_created_user_id = $5
                        WHERE qt_id = $6
            """
            question_generate = await conn.execute(query, question_gen.q_numb_to_generate, current_q_num, current_q_num, now, int(user_id),
                                             question_gen.qt_id)
            return Response(
                status_code=status.HTTP_200_OK,
                message="The request was successful",
                data={'output': output_dict},
                detail=None
            )
        elif question_gen.action_code == 0:
            output_dict = deepcopy(ast.literal_eval(p.stdout.splitlines()[p.stdout.splitlines().index('fait_output') + 1]))
            now = datetime.utcnow()
            query = """
                                    UPDATE question_gen_manager
                                    SET q_num_add_to_db = $1, q_num_db = $2, q_unused_db = $3, time_last_edited = $4, last_created_user_id = $5
                                    WHERE qt_id = $6
                        """
            question_generate = await conn.execute(query, question_gen.q_numb_to_generate, current_q_num, current_q_num,
                                                   now, int(user_id),
                                                   question_gen.qt_id)
            return Response(
                status_code=status.HTTP_200_OK,
                message="The request was successful",
                data={'output': output_dict},
                detail=None
            )
        # print("output:", output_dict)


        # client = MongoClient(
        #     host=configfile["mongodb"]["host"],
        #     port=configfile["mongodb"]["port"],
        #     username=(base64.b64decode(configfile["mongodb"]["username"])).decode("utf-8"),
        #     password=(base64.b64decode(configfile["mongodb"]["password"])).decode("utf-8"),
        # )
        # db_name = question_gen.qt_id[:14]
        # db = client[db_name]
        # collection_name = question_gen.qt_id[:19]
        # collection = db[collection_name]
        # document_name = question_gen.qt_id + f"_{question_gen.q_var_to_generate}"
        #
        #
        # match_file = str(os.path.dirname(scriptDir) + "/utils/match.json")
        # with open(match_file, "r") as file:
        #     data = json.load(file)
        # collection.insert_one({f"{document_name}": data})
        # return {
        #     "message": f"Question ID {question_gen.qt_id} Successfully added",
        # }
        # p = question_generator(question.qt_id, question.q_numb_to_generate, question.q_var_to_generate, question.action_code, question.qt_format)
        # print("Here is the Error:", question_generator.stderr)
        #
        # if question.action_code == 1:
        #     output_dict = deepcopy(p.stdout.splitlines()[p.stdout.splitlines().index('fait_output')+1])
        # elif question.action_code == 0:
        #     output_dict = deepcopy(ast.literal_eval(p.stdout.splitlines()[p.stdout.splitlines().index('fait_output')+1]))
        #
        # print("output:", output_dict)
    except Exception as e:
        return str(e)


