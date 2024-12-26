from fastapi import APIRouter, Request, Header, HTTPException, status, Request, UploadFile
from fastapi import Response as resp
import asyncpg
import os
from utils.tools import find_country_code, save_user_token, find_user_id_by_token, connect_to_redis, count_records_by_user_id, \
    delete_user_tokens
from validations.question_type import (Response, QuestionType, DeleteQuestionType, UpdateQuestionType, read_country_json)
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict
from pydantic import BaseModel, ValidationError
import pytz
import yaml
import base64
import json
from io import BytesIO, StringIO
import csv

scriptDir = os.path.dirname(os.path.abspath(__file__))
configfile = {}
config_filepath = os.path.dirname(scriptDir)+"/configfile.yml"
country_json_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
country_json = country_json_dir +'/utils/country.json'

if os.path.exists(config_filepath):
    with open(config_filepath, 'rt') as configFile:
        try:
            configfile = yaml.safe_load(configFile.read())
        except Exception as e:
            print("Check the ConfigFile "+str(e))

router = APIRouter()

@router.post("/question_type/add", response_model=Response, summary="Create a new question_type",
             tags=["question_type"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful request",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "question type with ID {id} created successfully",
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

async def create_question_type(qt_type: QuestionType, token: str = Header(...)):
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
    query = "SELECT is_admin FROM users WHERE id = $1"
    is_admin = await conn.fetchval(query, int(user_id))
    await conn.close()

    if not is_admin:
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
        existing_id_s = await conn.fetchval(
            'SELECT id FROM learning_network WHERE ln_id = $1', qt_type.ln_id)
        if existing_id_s is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"The learning network id '{qt_type.ln_id}' is not exists in database.",
                data=None,
                detail=None
            )
        if qt_type.qual_dict is not None:
            for data in qt_type.qual_dict:
                existing_qual_data = await conn.fetchrow(
                    'SELECT * FROM qualification WHERE qual_id = $1', data['qualification_id'])
                if existing_qual_data is None:
                    return Response(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        message=f"This qualification id '{data['qualification_id']}' is not exists in qualification table.",
                        data=None,
                        detail=None
                    )
                existing_qual_data = dict(existing_qual_data)
                if existing_qual_data['title'] != data['qualification_title']:
                    return Response(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        message=f"This qualification title '{data['qualification_title']}' is not matching with existing title '{existing_qual_data['title']}' associated with qualification_id '{data['qualification_id']}' in database.",
                        data=None,
                        detail=None
                    )
                if data['qualification_study_level'] is not None and data['qualification_study_level'].strip() != "":
                    if data['qualification_study_level'] not in json.loads(existing_qual_data['study_level']):
                        return Response(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            message=f"This qualification study level '{data['qualification_study_level']}' is not exists in '{json.loads(existing_qual_data['study_level'])}' associated with qualification id '{existing_qual_data['qual_id']}' in database.",
                            data=None,
                            detail=None
                        )
                if data['qualification_grade'] is not None and data['qualification_grade'].strip() != "":
                    if data['qualification_grade'] not in json.loads(existing_qual_data['grade']):
                        return Response(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            message=f"This qualification grade '{data['qualification_grade']}' is not exists in '{json.loads(existing_qual_data['grade'])}' associated with qualification id '{existing_qual_data['qual_id']}' in database.",
                            data=None,
                            detail=None
                        )
                if data['qualification_variations'] is not None:
                    for i in data['qualification_variations']:
                        if i not in json.loads(existing_qual_data['var']):
                            return Response(
                                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                message=f"This qualification variation '{i}' is not exists in '{json.loads(existing_qual_data['var'])}' associated with qualification id '{existing_qual_data['qual_id']}' in database.",
                                data=None,
                                detail=None
                            )
                if data['qualification_module'] is not None:
                    for i in data['qualification_module']:
                        if i not in json.loads(existing_qual_data['modules']):
                            return Response(
                                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                message=f"This qualification module '{i}' is not exists in '{json.loads(existing_qual_data['modules'])}' associated with qualification id '{existing_qual_data['qual_id']}' in database.",
                                data=None,
                                detail=None
                            )
                if data['qualification_organisation'] is not None:
                    for i in data['qualification_organisation']:
                        if i not in json.loads(existing_qual_data['org']):
                            return Response(
                                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                message=f"This qualification organisation '{i}' is not exists in '{json.loads(existing_qual_data['org'])}' associated with qualification id '{existing_qual_data['qual_id']}' in database.",
                                data=None,
                                detail=None
                            )

        if qt_type.qt_order is not None:
            query = "SELECT max_order FROM learning_network WHERE ln_id = $1"
            max_qt_order = await conn.fetchval(query, qt_type.ln_id)
            query = "SELECT qt_order FROM question_type WHERE ln_id = $1"
            existing_qt_order = await conn.fetch(query, qt_type.ln_id)
            existing_qt_order_list = {record['qt_order'] for record in existing_qt_order}
            if qt_type.qt_order > max_qt_order:
                return Response(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    message=f"This qt_order '{qt_type.qt_order}' must be less the or equal to max_order of learning network '{max_qt_order}'.",
                    data=None,
                    detail=None
                )
            if qt_type.qt_order in existing_qt_order_list:
                return Response(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    message=f"This qt_order '{qt_type.qt_order}' already in database.",
                    data=None,
                    detail=None
                )

        # Check if a qualification with the same details already exists
        query = """SELECT id FROM question_type WHERE qt_id = $1"""

        existing_id = await conn.fetchval(query, qt_type.qt_id)
        if existing_id:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"This question type id '{qt_type.qt_id}' already exists in question_type table."
            )

        if qt_type.parent_nodes is not None:
            for i in qt_type.parent_nodes:
                if len(i) != 25:
                    return Response(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        message=f"The parent nodes list must has same level of question types, but it has '{i}'"
                    )

        # Insert the new qualification record without qual_id
        now = datetime.utcnow()
        insert_query = """
            INSERT INTO question_type (
                qt_id, title, ln_id, parent_nodes, qual_dict, qt_age, qt_format, qt_order, repeatable_pattern, period_pattern, country_id, page_script, is_non_calculator, min_time, max_time, end_time, learning_content, time_last_edited, last_created_user_id
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19
            )
            RETURNING id
        """
        parent = json.dumps(qt_type.parent_nodes) if qt_type.parent_nodes else None
        question_type_id = await conn.fetchval(
            insert_query,
            qt_type.qt_id,
            qt_type.title,
            qt_type.ln_id,
            parent,
            json.dumps(qt_type.qual_dict),
            qt_type.qt_age,
            qt_type.qt_format,
            qt_type.qt_order,
            qt_type.repeatable_pattern,
            qt_type.period_pattern if qt_type.period_pattern else None,
            json.dumps(qt_type.country_id),
            qt_type.page_script if qt_type.page_script else None,
            qt_type.is_non_calculator,
            qt_type.min_time,
            qt_type.max_time,
            qt_type.end_time,
            qt_type.learning_content if qt_type.learning_content else None,
            now,
            int(user_id)
        )
        return Response(
            status_code=status.HTTP_200_OK,
            message=f"Question_type with ID {question_type_id} created successfully",
            data=None,
            detail=None
        )
    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create question_type: {str(e)}"
        )
    finally:
        await conn.close()



@router.get("/question_type", response_model=Response, summary="Get all question_type",
            tags=["question_type"],
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
                                        "title": "Mathematics",
                                        "ln_id": "001a-001a-001a-001a",
                                        "parent_nodes": "[001a-001a-001a-001a-0001a, 001a-001a-001a-001a-0002a]",
                                        "qual_dict": [{},{}],
                                        "qt_age": 25,
                                        "qt_format": 'match',
                                        "qt_order": 1,
                                        "repeatable_pattern": "3|1|1",
                                        "period_pattern": "60|90",
                                        "time_created": "2024-08-05T12:00:00Z",
                                        "time_last_edited": "2024-08-05T12:00:00Z",
                                        "last_edited_user_email": "user@example.com",
                                        "country_id": ["GB", "IN"],
                                        "page_script": "<script>",
                                        "is_non_calculator": True,
                                        "min_time": 5,
                                        "max_time": 10,
                                        "end_time": 15,
                                        "learning_content": "<Welcome>"

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
async def get_question_type(token: str = Header(...)):
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
    query = "SELECT is_admin FROM users WHERE id = $1"
    is_admin = await conn.fetchval(query, int(user_id))
    await conn.close()

    if not is_admin:
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

        # Fetch all question_type from the database
        query = """
                SELECT id, qt_id, title, ln_id, parent_nodes, qual_dict, qt_age, qt_format, qt_order, repeatable_pattern, period_pattern, country_id, page_script, is_non_calculator, min_time, max_time, end_time, learning_content, time_created, time_last_edited, last_created_user_id
                FROM question_type
                """
        question_type = await conn.fetch(query)

        # Prepare user emails for each qualification
        question_type_list = []
        for qual in question_type:
            timestamp0 = qual['time_created'].replace(tzinfo=pytz.UTC).timestamp()

            timestamp = qual['time_last_edited'].replace(tzinfo=pytz.UTC).timestamp()
            # Convert comma-separated strings to lists
            question_type_data = {
                "id": qual['id'],
                "qt_id": qual['qt_id'],
                "title": qual['title'],
                "ln_id": qual['ln_id'],
                "parent_nodes": json.loads(qual['parent_nodes']) if qual['parent_nodes'] else None,
                "qual_dict": json.loads(qual['qual_dict']),
                "qt_age": qual['qt_age'],
                "qt_format":qual['qt_format'],
                "qt_order":qual['qt_order'],
                "repeatable_pattern": qual['repeatable_pattern'],
                "period_pattern": qual["period_pattern"] if qual["period_pattern"] else None,
                "country_id": json.loads(qual["country_id"]),
                "page_script": qual["page_script"] if qual['page_script'] else None,
                "is_non_calculator": qual["is_non_calculator"] ,
                "min_time": qual["min_time"],
                "max_time": qual["max_time"],
                "end_time": qual["end_time"],
                "learning_content": qual["learning_content"] if qual['learning_content'] else None,
                "time_created": timestamp0,
                "time_last_edited": timestamp
            }

            # Fetch user email
            user_query = "SELECT email FROM users WHERE id = $1"
            user_email = await conn.fetchval(user_query, int(qual['last_created_user_id']))
            question_type_data["last_edited_user_email"] = user_email

            question_type_list.append(question_type_data)
        return Response(
            status_code=status.HTTP_200_OK,
            message="The request was successful",
            data=question_type_list,
            detail=None
        )

    except Exception as e:
        return dict(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to retrieve question_type: {str(e)}",
            data=None,
            detail=None
        )

    finally:
        await conn.close()

@router.post("/question_type/delete", response_model=Response, summary="Delete an existing question_type",
             tags=["question_type"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful request",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "question_type with ID {qt_id} deleted successfully",
                                 "data": {"qual_id": 1},
                                 "detail": None
                             }
                         }
                     }
                 },
                 422: {
                     "model": Response,
                     "description": "Validation error (e.g., invalid session ID or forbidden access)",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 422,
                                 "message": "Validation error",
                                 "data": None,
                                 "detail": [
                                     {"loc": ["header", "token"], "msg": "Invalid session ID", "type": "value_error"},
                                     {"loc": [], "msg": "You do not have permission to perform this action",
                                      "type": "access_error"}
                                 ]
                             }
                         }
                     }
                 }
             })
async def delete_question_type(question_type_delete: DeleteQuestionType, token: str = Header(...)):
    # Check user authentication based on token
    loop = asyncio.get_running_loop()
    user_id = await loop.run_in_executor(ThreadPoolExecutor(), find_user_id_by_token, token)

    if not user_id:
        return Response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Invalid session ID",
            data=None,
            detail=None
        )

    # Check if user is admin
    conn = await asyncpg.connect(
        user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
        database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
        host=str(configfile["database"]["host"]),
        port=str(configfile["database"]["port"])
    )
    try:
        query = "SELECT is_admin FROM users WHERE id = $1"
        is_admin = await conn.fetchval(query, int(user_id))

        if not is_admin:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="You do not have permission to perform this action",
                data=None,
                detail=None
            )

        # Delete the qualification from the database
        query = """
                DELETE FROM question_type
                WHERE id = $1
                RETURNING qt_id
                """
        deleted_question_type_id = await conn.fetchval(query, question_type_delete.id)

        if deleted_question_type_id:
            return Response(
                status_code=status.HTTP_200_OK,
                message=f"Question_type with ID {deleted_question_type_id} deleted successfully",
                data={"qt_id": deleted_question_type_id},
                detail=None
            )
        else:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Question_type deletion failed",
                data=None,
                detail=None
            )
    except Exception as e:
        return Response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=f"Failed to delete question_type: {str(e)}",
            data=None,
            detail=None
        )

@router.post("/question_type/edit", response_model=Response, summary="Update an existing question_type",
             tags=["question_type"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful request",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "question_type with ID {id} updated successfully",
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
async def update_question_type(question_type_update: UpdateQuestionType, token: str = Header(...)):
    loop = asyncio.get_running_loop()
    user_id = await loop.run_in_executor(ThreadPoolExecutor(), find_user_id_by_token, token)
    if not user_id:
        return Response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid session ID"
        )

    conn = await asyncpg.connect(
        user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
        database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
        host=str(configfile["database"]["host"]),
        port=str(configfile["database"]["port"])
    )
    query = "SELECT is_admin FROM users WHERE id = $1"
    is_admin = await conn.fetchval(query, int(user_id))
    await conn.close()
    if not is_admin:
        return Response(
            status_code=status.HTTP_403_FORBIDDEN,
            message="You do not have permission to perform this action"
        )

    conn = await asyncpg.connect(
        user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
        database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
        host=str(configfile["database"]["host"]),
        port=str(configfile["database"]["port"])
    )
    try:
        # Check if the qualification exists
        existing_question_type = await conn.fetchrow('SELECT * FROM question_type WHERE id = $1',
                                                     question_type_update.id)
        if existing_question_type is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="question_type not found",
                data=None,
                detail=None
            )
        existing_id_s = await conn.fetchval(
            'SELECT * FROM learning_network WHERE ln_id = $1', question_type_update.ln_id)
        if existing_id_s is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"The learning_network id '{question_type_update.ln_id}' is not exists in database.",
                data=None,
                detail=None
            )
        if question_type_update.qual_dict is not None:
            for data in question_type_update.qual_dict:
                existing_qual_data = await conn.fetchrow(
                    'SELECT * FROM qualification WHERE qual_id = $1', data['qualification_id'])
                if existing_qual_data is None:
                    return Response(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        message=f"This qualification id '{data['qualification_id']}' is not exists in qualification table.",
                        data=None,
                        detail=None
                    )
                existing_qual_data = dict(existing_qual_data)
                if existing_qual_data['title'] != data['qualification_title']:
                    return Response(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        message=f"This qualification title '{data['qualification_title']}' is not matching with existing title '{existing_qual_data['title']}' associated with qualification_id '{data['qualification_id']}' in database.",
                        data=None,
                        detail=None
                    )
                if data['qualification_study_level'] is not None and data['qualification_study_level'].strip() != "":
                    if data['qualification_study_level'] not in json.loads(existing_qual_data['study_level']):
                        return Response(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            message=f"This qualification study level '{data['qualification_study_level']}' is not exists in '{json.loads(existing_qual_data['study_level'])}' associated with qualification id '{existing_qual_data['qual_id']}' in database.",
                            data=None,
                            detail=None
                        )
                if data['qualification_grade'] is not None and data['qualification_grade'].strip() != "":
                    if data['qualification_grade'] not in json.loads(existing_qual_data['grade']):
                        return Response(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            message=f"This qualification grade '{data['qualification_grade']}' is not exists in '{json.loads(existing_qual_data['grade'])}' associated with qualification id '{existing_qual_data['qual_id']}' in database.",
                            data=None,
                            detail=None
                        )
                if data['qualification_variations'] is not None:
                    for i in data['qualification_variations']:
                        if i not in json.loads(existing_qual_data['var']):
                            return Response(
                                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                message=f"This qualification variation '{i}' is not exists in '{json.loads(existing_qual_data['var'])}' associated with qualification id '{existing_qual_data['qual_id']}' in database.",
                                data=None,
                                detail=None
                            )
                if data['qualification_module'] is not None:
                    for i in data['qualification_module']:
                        if i not in json.loads(existing_qual_data['modules']):
                            return Response(
                                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                message=f"This qualification module '{i}' is not exists in '{json.loads(existing_qual_data['modules'])}' associated with qualification id '{existing_qual_data['qual_id']}' in database.",
                                data=None,
                                detail=None
                            )
                if data['qualification_organisation'] is not None:
                    for i in data['qualification_organisation']:
                        if i not in json.loads(existing_qual_data['org']):
                            return Response(
                                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                message=f"This qualification organisation '{i}' is not exists in '{json.loads(existing_qual_data['org'])}' associated with qualification id '{existing_qual_data['qual_id']}' in database.",
                                data=None,
                                detail=None
                            )
        if question_type_update.qt_order is not None:
            if question_type_update.qt_order != existing_question_type["qt_order"]:
                query = "SELECT max_order FROM learning_network WHERE ln_id = $1"
                max_qt_order = await conn.fetchval(query, question_type_update.ln_id)
                query = "SELECT qt_order FROM question_type WHERE ln_id = $1"
                existing_qt_order = await conn.fetch(query, question_type_update.ln_id)
                existing_qt_order_list = {record['qt_order'] for record in existing_qt_order}
                if question_type_update.qt_order > max_qt_order:
                    return Response(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        message=f"This qt_order '{question_type_update.qt_order}' must be less the or equal to max_order of learning network '{max_qt_order}'.",
                        data=None,
                        detail=None
                    )
                if question_type_update.qt_order in existing_qt_order_list:
                    return Response(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        message=f"This qt_order '{question_type_update.qt_order}' already in database.",
                        data=None,
                        detail=None
                    )
        if question_type_update.parent_nodes is not None:
            for i in question_type_update.parent_nodes:
                if len(i) != 25:
                    return Response(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        message=f"The parent nodes list must has same level of question types, but it has '{i}'."
                    )
        # Prepare fields for update
        update_fields = []
        update_values = []
        # parent = ','.join(question_type_update.parent_nodes) if question_type_update.parent_nodes else None
        parent = json.dumps(question_type_update.parent_nodes) if question_type_update.parent_nodes else None
        if (existing_question_type["qt_id"] == question_type_update.qt_id and existing_question_type["title"] == question_type_update.title and
                existing_question_type["ln_id"] == question_type_update.ln_id and sorted(existing_question_type["qual_dict"]) == sorted(json.dumps(question_type_update.qual_dict)) and
                existing_question_type["qt_age"] == question_type_update.qt_age and existing_question_type["qt_format"] == question_type_update.qt_format and
                existing_question_type["qt_order"] == question_type_update.qt_order and existing_question_type["repeatable_pattern"] == question_type_update.repeatable_pattern and
                existing_question_type["period_pattern"] == question_type_update.period_pattern and existing_question_type["country_id"] == json.dumps(question_type_update.country_id) and
                existing_question_type["page_script"] == question_type_update.page_script and existing_question_type["is_non_calculator"] == question_type_update.is_non_calculator and
                existing_question_type["min_time"] == question_type_update.min_time and existing_question_type["max_time"] == question_type_update.max_time and existing_question_type["end_time"] == question_type_update.end_time and
                existing_question_type["learning_content"] == question_type_update.learning_content and existing_question_type["parent_nodes"] == parent):
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="No data has been changed, no editing is done",
                data=None,
                detail=None
            )
        if question_type_update.qt_id is not None:
            if existing_question_type['qt_id'] != question_type_update.qt_id:
                existing_id = await conn.fetchval(
                    'SELECT * FROM question_type WHERE qt_id = $1',
                    question_type_update.qt_id)
                if existing_id:
                    return Response(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        message=f"This question type id '{question_type_update.qt_id}' already exists in database.",
                        data=None,
                        detail=None
                    )
            update_fields.append("qt_id = $1")
            update_values.append(question_type_update.qt_id)
        if question_type_update.title is not None:
            update_fields.append("title = $2")
            update_values.append(question_type_update.title)
        if question_type_update.ln_id is not None:
            update_fields.append("ln_id = $3")
            update_values.append(question_type_update.ln_id)
        if question_type_update.parent_nodes is not None:
            update_fields.append("parent_nodes = $4")
            update_values.append(parent)
        else:
            update_fields.append("parent_nodes = $4")
            update_values.append(question_type_update.parent_nodes)
        if question_type_update.qual_dict is not None:
            update_fields.append("qual_dict = $5")
            update_values.append(json.dumps(question_type_update.qual_dict))
        if question_type_update.qt_age is not None:
            update_fields.append("qt_age = $6")
            update_values.append(question_type_update.qt_age)
        if question_type_update.qt_format is not None:
            update_fields.append("qt_format = $7")
            update_values.append(question_type_update.qt_format)
        if question_type_update.qt_order is not None:
            update_fields.append("qt_order = $8")
            update_values.append(question_type_update.qt_order)
        if question_type_update.repeatable_pattern is not None:
            update_fields.append("repeatable_pattern = $9")
            update_values.append(question_type_update.repeatable_pattern)
        if question_type_update.period_pattern is not None:
            update_fields.append("period_pattern = $10")
            update_values.append(question_type_update.period_pattern)
        else:
            update_fields.append("period_pattern = $10")
            update_values.append(question_type_update.period_pattern)
        if question_type_update.country_id is not None:
            update_fields.append("country_id = $11")
            update_values.append(json.dumps(question_type_update.country_id))
        if question_type_update.page_script is not None:
            update_fields.append("page_script = $12")
            update_values.append(question_type_update.page_script)
        else:
            update_fields.append("page_script = $12")
            update_values.append(question_type_update.page_script)
        if question_type_update.is_non_calculator is not None:
            update_fields.append("is_non_calculator = $13")
            update_values.append(question_type_update.is_non_calculator)
        if question_type_update.min_time is not None:
            update_fields.append("min_time = $14")
            update_values.append(question_type_update.min_time)
        if question_type_update.max_time is not None:
            update_fields.append("max_time = $15")
            update_values.append(question_type_update.max_time)
        if question_type_update.end_time is not None:
            update_fields.append("end_time = $16")
            update_values.append(question_type_update.end_time)
        if question_type_update.learning_content is not None:
            update_fields.append("learning_content = $17")
            update_values.append(question_type_update.learning_content)
        else:
            update_fields.append("learning_content = $17")
            update_values.append(question_type_update.learning_content)


        if not update_fields:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="No fields to update",
                data=None,
                detail=None
            )
        now = datetime.utcnow()
        # Add fields for user ID and timestamp
        update_fields.extend(["time_last_edited = $18", "last_created_user_id = $19"])
        update_values.extend([now, int(user_id)])
        update_query = f"""
            UPDATE question_type
            SET {', '.join(update_fields)}
            WHERE id = ${20}
        """
        update_values.append(question_type_update.id)
        await conn.execute(update_query, *update_values)

        return Response(
            status_code=status.HTTP_200_OK,
            message=f"Question_type with ID {question_type_update.id} updated successfully",
            data=None,
            detail=None
        )

    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to update question_type: {str(e)}",
            data=None,
            detail=None
        )
    finally:
        await conn.close()

@router.get("/question_type/download", summary="Download all question_types", tags=["question_type"])
async def download_question_type(token: str = Header(...)):
    # Check user authentication based on token
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
    query = "SELECT is_admin FROM users WHERE id = $1"
    is_admin = await conn.fetchval(query, int(user_id))
    await conn.close()
    if not is_admin:
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
        query = """
                SELECT id, qt_id, title, ln_id, parent_nodes, qual_dict, qt_age, qt_format, qt_order, repeatable_pattern, period_pattern, country_id, page_script, is_non_calculator, min_time, max_time, end_time, learning_content, time_created, time_last_edited, last_created_user_id
                FROM question_type  
                """
        records = await conn.fetch(query)
        question_type_list = [dict(record) for record in records]
        await conn.close()
        headers = ['id', 'qt_id', 'title', 'ln_id', 'parent_nodes', 'qual_dict', 'qt_age', 'qt_format', 'qt_order', 'repeatable_pattern', 'period_pattern', 'country_id', 'page_script', 'is_non_calculator', 'min_time', 'max_time', 'end_time', 'learning_content', 'time_created', 'time_last_edited', 'last_created_user_id']
        scriptDir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = scriptDir + f'/fait_back_res/backend_data_rep/question_type_download_{timestamp}.csv'
        with open(file_path, 'w', newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers, restval="", extrasaction='ignore', lineterminator="\n")
            writer.writeheader()
            for record in question_type_list:
                writer.writerow(record)

        return Response(
            status_code=status.HTTP_200_OK,
            message=f"File created successfully.",
            data={'filename': f'question_type_download_{timestamp}.csv'},
            detail=None
        )
    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to download question_type: {str(e)}",
            data=None,
            detail=None
        )

@router.post("/question_type/upload", summary="Upload question_type", tags=["question_type"])
async def upload_question_type(file: UploadFile, token: str = Header(...)):
    if file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="File must be in CSV format")
    # Check user authentication based on token
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
    query = "SELECT is_admin FROM users WHERE id = $1"
    is_admin = await conn.fetchval(query, int(user_id))
    await conn.close()
    if not is_admin:
        return Response(
            status_code=status.HTTP_403_FORBIDDEN,
            message="You do not have access to this section",
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
    existing_qt_ids = await conn.fetch("SELECT qt_id from question_type")
    existing_qt_records = {record['qt_id'] for record in existing_qt_ids}
    existing_ln_ids = await conn.fetch("SELECT ln_id from learning_network")
    existing_ln_records = {record['ln_id'] for record in existing_ln_ids}
    try:
        content = await file.read()
        csv_data = content.decode('utf-8').splitlines()
        reader = csv.DictReader(csv_data)
        new_ln_ids = []
        unsuccessful_list = []
        for row in reader:
            validation = True
            qt_id = row['qt_id']
            ln_id = row['ln_id']
            parent_nodes = row['parent_nodes']
            qual_dict = json.loads(row['qual_dict'])
            repeatable_pattern = row['repeatable_pattern']
            period_pattern = row['period_pattern']
            country_id = row['country_id']
            is_non_calculator = row['is_non_calculator']

            try:
                ln_id = ln_id + '-'
                if ln_id != qt_id[:20]:
                    validation = False
                parts = qt_id.split('-')
                for i in range(len(parts) - 1):
                    if i != len(parts) - 1:
                        if len(parts[i]) != 4:
                            validation = False
                        if not parts[i][:3].isdigit():
                            validation = False
                        if not parts[i][3].islower():
                            validation = False
                if len(parts[-1]) != 5:
                    validation = False
                if not parts[-1][:4].isdigit():
                    validation = False
                if not parts[-1][4].islower():
                    validation = False
                if parent_nodes is not None:
                    parent_nodes = json.loads(row['parent_nodes'])
                    for i in parent_nodes:
                        if i != '':
                            if len(i) != 25:
                                validation = False

                qual_dict_ids = [item['qualification_id'] for item in qual_dict]
                if len(qual_dict_ids) != len(set(qual_dict_ids)):
                    validation = False
                existing_qual_data = await conn.fetchrow(
                    'SELECT * FROM qualification WHERE qual_id = $1', qual_dict['qualification_id'])
                existing_qual_data = dict(existing_qual_data)
                qualification_variations = json.loads(existing_qual_data['var'])
                qualification_organisation = json.loads(existing_qual_data['org'])
                qualification_study_level = json.loads(existing_qual_data['study_level'])
                qualification_grade = json.loads(existing_qual_data['grade'])
                qualification_module = json.loads(existing_qual_data['modules'])
                for item in qual_dict:
                    if item['qualification_title'] is None:
                        validation = False
                    if item['qualification_variations'] is not None:
                        for item_lst in item['qualification_variations']:
                            if item_lst not in qualification_variations:
                                validation = False
                    if item['qualification_organisation'] is not None:
                        for item_lst in item['qualification_organisation']:
                            if item_lst not in qualification_organisation:
                                validation = False
                    if item['qualification_study_level'] is not None:
                        if item['qualification_study_level'] not in qualification_study_level:
                            validation = False
                    if item['qualification_grade'] is not None:
                        if item['qualification_grade'] not in qualification_grade:
                            validation = False
                    if item['qualification_module'] is not None:
                        if item['qualification_module'] not in qualification_module:
                            validation = False

                rp_parts = repeatable_pattern.split('|')
                for i in rp_parts:
                    if not i.isdigit():
                        validation = False
                if len(rp_parts) == 1:
                    if period_pattern is not None:
                        validation = False
                if len(rp_parts) > 1:
                    if period_pattern is None:
                        validation = False
                if period_pattern is not None:
                    pp_parts = period_pattern.split('|')
                    for i in pp_parts:
                        if not i.isdigit():
                            validation = False
                        if len(pp_parts) != len(rp_parts)-1:
                            validation = False
                if country_id is None or country_id == []:
                    validation = False
                if country_id is not None:
                    for country in country_id:
                        country_list = read_country_json(country_json)
                        if country not in country_list:
                            validation = False
                        if len(country) != 2 or not country.isupper():
                            validation = False

            except Exception as e:
                validation = False

            if row['ln_id'] in existing_ln_records and row['qt_id'] not in existing_qt_records and validation == True:
                conn = await asyncpg.connect(
                    user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
                    password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
                    database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
                    host=str(configfile["database"]["host"]),
                    port=str(configfile["database"]["port"])
                )
                now = datetime.utcnow()
                insert_query = """
                            INSERT INTO question_type (
                                qt_id, title, ln_id, parent_nodes, qual_dict, qt_age, qt_format, qt_order, repeatable_pattern, period_pattern, country_id, page_script, is_non_calculator, min_time, max_time, end_time, learning_content, time_last_edited, last_created_user_id
                            ) VALUES (
                                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19
                            )
                            RETURNING id
                        """

                row['is_non_calculator'] = row['is_non_calculator'].strip().lower() == 'true'
                question_type_id = await conn.fetchval(
                    insert_query,
                    row['qt_id'],
                    row['title'],
                    row['ln_id'],
                    row['parent_nodes'] if row['parent_nodes'] else None,
                    row['qual_dict'],
                    int(row['qt_age']),
                    row['qt_format'],
                    int(row['qt_order']),
                    row['repeatable_pattern'],
                    row['period_pattern'] if row['period_pattern'] else None,
                    row['country_id'],
                    row['page_script'] if row['page_script'] else None,
                    row['is_non_calculator'],
                    int(row['min_time']),
                    int(row['max_time']),
                    int(row['end_time']),
                    row['learning_content'] if row['learning_content'] else None,
                    now,
                    int(user_id)
                )
                new_ln_ids.append(question_type_id)
            else:
                unsuccessful_list.append(row['ln_id'])
        return Response(
            status_code=status.HTTP_200_OK,
            message=f"Question_type with IDs {new_ln_ids} created successfully and Unsuccessful IDs are {unsuccessful_list}",
            data=None,
            detail=None
        )
    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create question_type IDs: {str(e)}"
        )