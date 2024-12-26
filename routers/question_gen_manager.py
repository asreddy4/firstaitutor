import os
from fastapi import APIRouter, Request, Header, HTTPException, status, Request, UploadFile
import asyncpg
from utils.tools import find_country_code, save_user_token, find_user_id_by_token, connect_to_redis, count_records_by_user_id, \
    delete_user_tokens
from validations.question_gen_manager import QuestionTypeRegister, QuestionCreatorApproval, QuestionGen, QuestionManagerApproval, Response
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict
from pydantic import BaseModel, ValidationError
import pytz
import yaml
import base64
import json
import csv

scriptDir = os.path.dirname(os.path.abspath(__file__))
configfile = {}
config_filepath = os.path.dirname(scriptDir)+"/configfile.yml"
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

@router.post("/question_type/register", response_model=Response, summary="Register a question_type",
             tags=["question_gen_manager"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful request",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "Question type {id} successfully registered",
                                 "data": None,
                                 "detail": None
                             }
                         }
                     }
                 },
                 422: {
                     "model": Response,
                     "description": "Validation error (e.g., invalid input data)",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 422,
                                 "message": "Validation error",
                                 "data": None,
                                 "detail": [
                                     {"loc": [], "msg": "Invalid input data", "type": "value_error"}
                                 ]
                             }
                         }
                     }
                 }
             })

async def register_question_type(qt_register: QuestionTypeRegister, token: str = Header(...)):
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

    if existing_user['user_type'] not in {"admin", "content_manager", "super_admin"}:
        return Response(
            status_code=status.HTTP_403_FORBIDDEN,
            message="You do not have access to this section",
            data=None,
            detail=None
        )
    try:
        conn = await asyncpg.connect(
            user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
            password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
            database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
            host=str(configfile["database"]["host"]),
            port=str(configfile["database"]["port"])
        )
        existing_qt = await conn.fetchrow(
            'SELECT * FROM question_type WHERE qt_id = $1', qt_register.qt_id)
        if existing_qt is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"The question type id '{qt_register.qt_id}' is not exists in question_type table.",
                data=None,
                detail=None
            )
        existing_qts = await conn.fetchrow(
            'SELECT * FROM question_gen_manager WHERE qt_id = $1 and q_variation = $2', qt_register.qt_id, qt_register.q_variation
        )
        if existing_qts:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"The qt_id '{qt_register.qt_id}' with variation '{qt_register.q_variation}' is already exists in question_gen_manager table.",
                data=None,
                detail=None
            )
        question_variations_json = read_question_variations(question_variations)
        variations_list = {i for i in question_variations_json.values()}
        if qt_register.q_variation is not None:
            if qt_register.q_variation not in variations_list:
                return Response(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    message=f"The question variation '{qt_register.q_variation}' is not exists in '{variations_list}'.",
                    data=None,
                    detail=None
                )
        existing_admin_users = await conn.fetch(
            'SELECT fullname FROM admins WHERE user_type = ANY($1)', ['admin', 'super_admin', 'content_manager', 'question_creator']
        )
        existing_admin_users_list = [record['fullname'] for record in existing_admin_users]
        if qt_register.q_assigned_to not in existing_admin_users_list:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"There is no user with name '{qt_register.q_assigned_to}' exists in database.",
                data=None,
                detail=None
            )
        now = datetime.utcnow()
        insert_query = """
                INSERT INTO question_gen_manager (
                    qt_id, qt_title, qt_format, q_variation, q_spec, q_assigned_to, q_manager_name, time_last_edited, last_created_user_id
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9
                )
                RETURNING qt_id
        """
        question_gen_id = await conn.fetchval(
            insert_query,
            qt_register.qt_id,
            existing_qt['title'],
            existing_qt['qt_format'],
            qt_register.q_variation,
            qt_register.q_spec,
            qt_register.q_assigned_to,
            existing_user['fullname'],
            now,
            int(user_id)
        )

        return Response(
            status_code=status.HTTP_200_OK,
            message=f"Question_type ID {question_gen_id} registered successfully",
            data=None,
            detail=None
        )

    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create question: {str(e)}"
        )
    finally:
        await conn.close()

@router.post("/question/creator/approve", response_model=Response, summary="Approve question by creator",
             tags=["question_gen_manager"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful request",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "Question {id} successfully approved.",
                                 "data": None,
                                 "detail": None
                             }
                         }
                     }
                 },
                 422: {
                     "model": Response,
                     "description": "Validation error (e.g., invalid input data)",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 422,
                                 "message": "Validation error",
                                 "data": None,
                                 "detail": [
                                     {"loc": [], "msg": "Invalid input data", "type": "value_error"}
                                 ]
                             }
                         }
                     }
                 }
             })

async def approve_question_by_creator(qt_approve: QuestionCreatorApproval, token: str = Header(...)):
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

    if existing_user['user_type'] not in {"question_creator", "admin", "content_manager", "super_admin"}:
        return Response(
            status_code=status.HTTP_403_FORBIDDEN,
            message="You do not have access to this section",
            data=None,
            detail=None
        )
    try:
        conn = await asyncpg.connect(
            user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
            password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
            database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
            host=str(configfile["database"]["host"]),
            port=str(configfile["database"]["port"])
        )
        existing_qts = await conn.fetchrow(
            'SELECT * FROM question_gen_manager WHERE qt_id = $1 and q_variation = $2 and q_assigned_to = $3', qt_approve.qt_id, qt_approve.q_variation, existing_user['fullname']
        )
        if existing_qts is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"The qt_id '{qt_approve.qt_id}' with variation '{qt_approve.q_variation}' is not exists or this question not assigned to '{existing_user['fullname']}'.",
                data=None,
                detail=None
            )
        # is_approved = await conn.fetchrow(
        #     'SELECT * FROM question_gen_manager WHERE qt_id = $1', qt_approve.qt_id
        # )
        if existing_qts['q_locked']:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"The question has already locked. Contact your manager.",
                data=None,
                detail=None
            )
        if existing_qts['q_manager_approved']:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"The question has already approved by question manager.",
                data=None,
                detail=None
            )
        if existing_qts['q_creator_approved']:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"The question has already approved by question creator.",
                data=None,
                detail=None
            )
        # existing_admin_users = await conn.fetch(
        #     'SELECT fullname FROM admins WHERE user_type = ANY($1)', ['admin', 'super_admin', 'content_manager']
        # )
        # existing_admin_users_list = [record['fullname'] for record in existing_admin_users]
        # if existing_admin_users is None:
        #     return Response(
        #         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        #         message=f"There is no admin user exists in database.",
        #         data=None,
        #         detail=None
        #     )
        if qt_approve.q_creator_approved is False:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"The question has to approve, It should be True.",
                data=None,
                detail=None
            )
        now = datetime.utcnow()
        query = """
                UPDATE question_gen_manager
                SET q_creator_approved = $1, q_locked = $2, time_last_edited = $3, last_created_user_id = $4
                WHERE qt_id = $5
            """
        qt_approved = await conn.execute(query, qt_approve.q_creator_approved, True, now, int(user_id), qt_approve.qt_id)
        return Response(
            status_code=status.HTTP_200_OK,
            message=f"The question with qt_id '{qt_approve.qt_id}' has been approved by creator '{existing_user['fullname']}' successfully.",
            data=None,
            detail=None
        )

    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create question: {str(e)}"
        )
    finally:
        await conn.close()

@router.post("/question/approve/manager", response_model=Response, summary="Approve question by manager",
             tags=["question_gen_manager"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful request",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "Question {id} successfully approved.",
                                 "data": None,
                                 "detail": None
                             }
                         }
                     }
                 },
                 422: {
                     "model": Response,
                     "description": "Validation error (e.g., invalid input data)",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 422,
                                 "message": "Validation error",
                                 "data": None,
                                 "detail": [
                                     {"loc": [], "msg": "Invalid input data", "type": "value_error"}
                                 ]
                             }
                         }
                     }
                 }
             })

async def approve_question_by_manager(qt_approve_manager: QuestionManagerApproval, token: str = Header(...)):
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

    if existing_user['user_type'] not in {"admin", "content_manager", "super_admin"}:
        return Response(
            status_code=status.HTTP_403_FORBIDDEN,
            message="You do not have access to this section",
            data=None,
            detail=None
        )
    try:
        conn = await asyncpg.connect(
            user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
            password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
            database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
            host=str(configfile["database"]["host"]),
            port=str(configfile["database"]["port"])
        )
        existing_qts = await conn.fetchrow(
            'SELECT * FROM question_gen_manager WHERE qt_id = $1 and q_variation = $2 and q_manager_name = $3', qt_approve_manager.qt_id, qt_approve_manager.q_variation, existing_user['fullname']
        )
        if existing_qts is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"The qt_id '{qt_approve_manager.qt_id}' with variation '{qt_approve_manager.q_variation}' is not exists or this question not assigned to '{existing_user['fullname']}'.",
                data=None,
                detail=None
            )
        existing_admin_users = await conn.fetch(
            'SELECT fullname FROM admins WHERE user_type = ANY($1)', ['admin', 'super_admin', 'content_manager']
        )
        existing_admin_users_list = [record['fullname'] for record in existing_admin_users]
        if existing_admin_users is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"There is no admin user exists in database.",
                data=None,
                detail=None
            )
        # is_approved = await conn.fetchrow(
        #     'SELECT * FROM question_gen_manager WHERE qt_id = $1', qt_approve_manager.qt_id
        # )
        if existing_qts['q_manager_approved']:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"The question has already approved by question manager.",
                data=None,
                detail=None
            )
        if qt_approve_manager.q_json_file_exist is False:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"Check the 'q_json_file_exist', It should be True.",
                data=None,
                detail=None
            )
        if qt_approve_manager.q_html_file_exist is False:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"Check the 'q_html_file_exist', It should be True.",
                data=None,
                detail=None
            )
        if qt_approve_manager.q_manager_approved is False:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"Check the 'q_manager_approved', It should be True.",
                data=None,
                detail=None
            )
        now = datetime.utcnow()
        query = """
                UPDATE question_gen_manager
                SET q_json_file_exist = $1, q_html_file_exist = $2, q_html_file_link = $3, q_manager_approved = $4, time_last_edited = $5, last_created_user_id = $6
                WHERE qt_id = $7
            """
        qt_approved_by_manager = await conn.execute(query, qt_approve_manager.q_json_file_exist, qt_approve_manager.q_html_file_exist, qt_approve_manager.q_html_file_link, qt_approve_manager.q_manager_approved, now, int(user_id), qt_approve_manager.qt_id)
        return Response(
            status_code=status.HTTP_200_OK,
            message=f"The question with qt_id '{qt_approve_manager.qt_id}' has been approved by manager '{existing_user['fullname']}' successfully.",
            data=None,
            detail=None
        )

    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create question: {str(e)}"
        )
    finally:
        await conn.close()


@router.get("/question_gen_manager", response_model=Response, summary="Get all data from question_gen_manager",
            tags=["question_gen_manager"],
            responses={
                200: {
                    "model": Response,
                    "description": "Successful request",
                    "content": {
                        "application/json": {
                            "example": {
                                "status_code": 200,
                                "message": "The request was successful",
                                "data": [
                                    {
                                        "id": 1,
                                        "qt_id": "001a-001a-001a-001a-0001a",
                                        "qt_title": "Match numbers between one and nine with their words",
                                        "qt_format": "match",
                                        "q_spec": "<h1>Welcome</h1>",
                                        "q_variation": 'englishuk',
                                        "q_assigned_to": "John Wick",
                                        "q_creator_approved": True,
                                        "q_num_db": 0,
                                        "q_unused_db": 0,
                                        "q_manager_name": "John Wick",
                                        "q_manager_approved": True,
                                        "q_lock": True,
                                        "q_json_file_exist": True,
                                        "q_html_file_exist": True,
                                        "q_html_file_link": "001a-001a-001a-001a-0001a.html",
                                        "set_edit_spec": {},
                                        "html_generated": "<Welcome>",
                                        "q_num_add_to_db": '',
                                        "q_logs": "Question created by John, 2024-12-16",
                                        "comments": "Registration Completed",
                                        "time_created": "2024-08-05T12:00:00Z",
                                        "time_last_edited": "2024-08-05T12:00:00Z",
                                        "last_edited_user_email": "user@example.com",

                                    }
                                ],
                                "detail": None
                            }
                        }
                    }
                },
                422: {
                    "model": Response,
                    "description": "Validation error (e.g., invalid input data)",
                    "content": {
                        "application/json": {
                            "example": {
                                "status_code": 422,
                                "message": "Validation error",
                                "data": None,
                                "detail": [
                                    {"loc": [], "msg": "Invalid input data", "type": "value_error"}
                                ]
                            }
                        }
                    }
                }
            })
async def get_question_gen_manager(token: str = Header(...)):
    loop = asyncio.get_running_loop()
    user_id = await loop.run_in_executor(None, find_user_id_by_token, token)

    if not user_id:
        return Response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid session ID",
            data=None,
            detail=None
        )

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

    if existing_user['user_type'] not in {"admin", "content_manager", "super_admin"}:
        return Response(
            status_code=status.HTTP_403_FORBIDDEN,
            message="You do not have access to this section",
            data=None,
            detail=None
        )

    try:
        conn = await asyncpg.connect(
            user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
            password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
            database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
            host=str(configfile["database"]["host"]),
            port=str(configfile["database"]["port"])
        )

        # Fetch all question_gen_manager from the database
        query = """
                SELECT id, qt_id, qt_title, qt_format, q_spec, q_variation, q_assigned_to, q_creator_approved, q_num_db, q_unused_db, q_manager_name, q_manager_approved, q_locked, q_json_file_exist, q_html_file_exist, q_html_file_link, set_edit_spec, html_generated, q_num_add_to_db, q_logs, comment, time_created, time_last_edited, last_created_user_id
                FROM question_gen_manager
                """
        question_gen_manager = await conn.fetch(query)

        # Prepare user emails for each qualification
        question_gen_manager_list = []
        for data in question_gen_manager:
            timestamp0 = data['time_created'].replace(tzinfo=pytz.UTC).timestamp()

            timestamp = data['time_last_edited'].replace(tzinfo=pytz.UTC).timestamp()
            # Convert comma-separated strings to lists
            question_gen_manager_data = {
                "id": data['id'],
                "qt_id": data['qt_id'] if data['qt_id'] else None,
                "qt_title": data['qt_title'] if data['qt_title'] else None,
                "qt_format": data['qt_format'] if data['qt_format'] else None,
                "q_spec": data['q_spec'] if data['q_spec'] else None,
                "q_variation": data['q_variation'] if data['q_variation'] else None,
                "q_assigned_to": data['q_assigned_to'] if data['q_assigned_to'] else None,
                "q_creator_approved": data['q_creator_approved'] if data['q_creator_approved'] else None,
                "q_num_db": data['q_num_db'] if data['q_num_db'] else None,
                "q_unused_db": data['q_unused_db'] if data['q_unused_db'] else None,
                "q_manager_name": data["q_manager_name"] if data["q_manager_name"] else None,
                "q_manager_approved": data["q_manager_approved"] if data["q_manager_approved"] else None,
                "q_locked": data["q_locked"] if data["q_locked"] else None,
                "q_json_file_exist": data["q_json_file_exist"] if data["q_json_file_exist"] else None,
                "q_html_file_exist": data["q_html_file_exist"] if data["q_html_file_exist"] else None,
                "q_html_file_link": data["q_html_file_link"] if data["q_html_file_link"] else None,
                "set_edit_spec": data["set_edit_spec"] if data["set_edit_spec"] else None,
                "html_generated": data["html_generated"] if data["html_generated"] else None,
                "q_num_add_to_db": data["q_num_add_to_db"] if data["q_num_add_to_db"] else None,
                "q_logs": data['q_logs'] if data['q_logs'] else None,
                "comment": data["comment"] if data["comment"] else None,
                "time_created": timestamp0,
                "time_last_edited": timestamp
            }
            # Fetch user email
            user_query = "SELECT email FROM admins WHERE id = $1"
            user_email = await conn.fetchval(user_query, int(data['last_created_user_id']))
            question_gen_manager_data["last_edited_user_email"] = user_email
            question_gen_manager_list.append(question_gen_manager_data)
        return Response(
            status_code=status.HTTP_200_OK,
            message="The request was successful",
            data=question_gen_manager_list,
            detail=None
        )

    except Exception as e:
        return dict(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to retrieve question_gen_manager: {str(e)}",
            data=None,
            detail=None
        )

    finally:
        await conn.close()

