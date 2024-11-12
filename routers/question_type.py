from fastapi import APIRouter, Request, Header, HTTPException, status, Request
from fastapi import Response as resp
import asyncpg
import os
from utils.tools import find_country_code, save_user_token, find_user_id_by_token, connect_to_redis, count_records_by_user_id, \
    delete_user_tokens
from validations.question_type import (Response, QuestionType, DeleteQuestionType, UpdateQuestionType)
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
                message=f"This learning network has not been registered with ID {existing_id_s if existing_id_s else qt_type.ln_id}",
                data=None,
                detail=None
            )
        if qt_type.q_dict is not None:
            for data in qt_type.q_dict:
                existing_q_id = await conn.fetchval(
                    'SELECT id FROM qualification WHERE q_id = $1', data['qualification_id'])
                if existing_q_id is None:
                    return Response(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        message=f"This qualification has not been registered with ID {existing_q_id if existing_q_id else qt_type.q_id}",
                        data=None,
                        detail=None
                    )
        # Check if a qualification with the same details already exists
        query = """SELECT id FROM question_type WHERE qt_id = $1"""

        existing_id = await conn.fetchval(query, qt_type.qt_id)
        if existing_id:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"This question type data has already been registered with ID {existing_id}"
            )

        # Insert the new qualification record without q_id
        now = datetime.utcnow()
        insert_query = """
            INSERT INTO question_type (
                qt_id, title, ln_id, q_dict, qt_age, qt_format, qt_order, repeatable_pattern, period_pattern, country_id, page_script, is_non_calculator, min_time, max_time, end_time, learning_content, time_last_edited, last_created_user_id
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18
            )
            RETURNING id
        """
        # parent = ','.join(ln_net.parent_nodes) if ln_net.parent_nodes else None
        question_type_id = await conn.fetchval(
            insert_query,
            qt_type.qt_id,
            qt_type.title,
            qt_type.ln_id,
            json.dumps(qt_type.q_dict),
            qt_type.qt_age,
            qt_type.qt_format,
            qt_type.qt_order,
            qt_type.repeatable_pattern,
            qt_type.period_pattern,
            qt_type.country_id,
            qt_type.page_script,
            qt_type.is_non_calculator,
            qt_type.min_time,
            qt_type.max_time,
            qt_type.end_time,
            qt_type.learning_content,
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
                                        "q_dict": [{},{}],
                                        "qt_age": 25,
                                        "qt_format": 1,
                                        "qt_order": 1,
                                        "repeatable_pattern": "3-1-1",
                                        "period_pattern": "60-90",
                                        "time_created": "2024-08-05T12:00:00Z",
                                        "time_last_edited": "2024-08-05T12:00:00Z",
                                        "last_edited_user_email": "user@example.com"
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

        # Fetch all qualifications from the database
        query = """
                SELECT id, qt_id, title, ln_id, q_dict, qt_age, qt_format, qt_order, repeatable_pattern, period_pattern, country_id, page_script, is_non_calculator, min_time, max_time, end_time, learning_content, time_created, time_last_edited, last_created_user_id
                FROM question_type
                """
        question_type = await conn.fetch(query)

        # Prepare user emails for each qualification
        question_type_list = []
        for qual in question_type:
            timestamp0 = qual['time_created'].replace(tzinfo=pytz.UTC).timestamp()

            timestamp = qual['time_last_edited'].replace(tzinfo=pytz.UTC).timestamp()
            # Convert comma-separated strings to lists
            ln_title = await conn.fetchval("""SELECT title FROM learning_network WHERE ln_id = $1""", qual['ln_id'])
            question_type_data = {
                "id": qual['id'],
                "qt_id": qual['qt_id'],
                "title": qual['title'],
                "ln_id": qual['ln_id'],
                "ln_title": ln_title,
                # "parent_nodes": qual['parent_nodes'].split(',') if qual['parent_nodes'] else [],
                "q_dict": qual['q_dict'],
                "qt-age": qual['qt_age'],
                "qt_format":qual['qt_format'],
                "qt_order":qual['qt_order'],
                "repeatable_pattern": qual['repeatable_pattern'],
                "period_pattern": qual["period_pattern"],
                "country_id": qual["country_id"],
                "page_script": qual["page_script"],
                "is_non_calculator": qual["is_non_calculator"],
                "min_time": qual["min_time"],
                "max_time": qual["max_time"],
                "end_time": qual["end_time"],
                "learning_content": qual["learning_content"],
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
            message=f"Failed to retrieve qualifications: {str(e)}",
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
                                 "data": {"q_id": 1},
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
                data={"ln_id": deleted_question_type_id},
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
                message=f"This learning_network has not been registered with ID {existing_id_s if existing_id_s else
                question_type_update.ln_id}",
                data=None,
                detail=None
            )
        if question_type_update.q_dict is not None:
            for data in question_type_update.q_dict:
                existing_q_id = await conn.fetchval(
                    'SELECT id FROM qualification WHERE q_id = $1', data['qualification_id'])
                if existing_q_id is None:
                    return Response(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        message=f"This qualification has not been registered with ID {existing_q_id if existing_q_id else question_type_update.q_id}",
                        data=None,
                        detail=None
                    )
        # Prepare fields for update
        update_fields = []
        update_values = []
        # parent = ','.join(question_type_update.parent_nodes) if question_type_update.parent_nodes else None
        if (existing_question_type["qt_id"] == question_type_update.qt_id and existing_question_type["title"] == question_type_update.title and existing_question_type["ln_id"] == question_type_update.ln_id and sorted(existing_question_type["q_dict"]) == sorted(json.dumps(question_type_update.q_dict)) and existing_question_type["qt_age"] == question_type_update.qt_age and existing_question_type["qt_format"] == question_type_update.qt_format and existing_question_type["qt_order"] == question_type_update.qt_order and existing_question_type["repeatable_pattern"] == question_type_update.repeatable_pattern and existing_question_type["period_pattern"] == question_type_update.period_pattern
                and existing_question_type["country_id"] == question_type_update.country_id) and existing_question_type["page_script"] == question_type_update.page_script and existing_question_type["is_non_calculator"] == question_type_update.is_non_calculator and existing_question_type["min_time"] == question_type_update.min_time and existing_question_type["max_time"] == question_type_update.max_time and existing_question_type["end_time"] == question_type_update.end_time and existing_question_type["learning_content"] == question_type_update.learning_content:
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
                        message=f"This qt_id has already been registered with ID {existing_id}",
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
        # if question_type_update.parent_nodes is not None:
        #     update_fields.append("parent_nodes = $4")
        #     update_values.append(parent)
        if question_type_update.q_dict is not None:
            update_fields.append("q_dict = $4")
            update_values.append(json.dumps(question_type_update.q_dict))
        if question_type_update.qt_age is not None:
            update_fields.append("qt_age = $5")
            update_values.append(question_type_update.qt_age)
        if question_type_update.qt_format is not None:
            update_fields.append("qt_format = $6")
            update_values.append(question_type_update.qt_format)
        if question_type_update.qt_order is not None:
            update_fields.append("qt_order = $7")
            update_values.append(question_type_update.qt_order)
        if question_type_update.repeatable_pattern is not None:
            update_fields.append("repeatable_pattern = $8")
            update_values.append(question_type_update.repeatable_pattern)
        if question_type_update.period_pattern is not None:
            update_fields.append("period_pattern = $9")
            update_values.append(question_type_update.period_pattern)
        if question_type_update.country_id is not None:
            update_fields.append("country_id = $10")
            update_values.append(question_type_update.country_id)
        if question_type_update.page_script is not None:
            update_fields.append("page_script = $11")
            update_values.append(question_type_update.page_script)
        if question_type_update.is_non_calculator is not None:
            update_fields.append("is_non_calculator = $12")
            update_values.append(question_type_update.is_non_calculator)
        if question_type_update.min_time is not None:
            update_fields.append("min_time = $13")
            update_values.append(question_type_update.min_time)
        if question_type_update.max_time is not None:
            update_fields.append("max_time = $14")
            update_values.append(question_type_update.max_time)
        if question_type_update.end_time is not None:
            update_fields.append("end_time = $15")
            update_values.append(question_type_update.end_time)
        if question_type_update.learning_content is not None:
            update_fields.append("learning_content = $16")
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
        update_fields.extend(["time_last_edited = $17", "last_created_user_id = $18"])
        update_values.extend([now, int(user_id)])

        update_query = f"""
            UPDATE question_type
            SET {', '.join(update_fields)}
            WHERE id = ${len(update_values) + 1}
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
            message=f"Failed to update qualification: {str(e)}",
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

    conn = await asyncpg.connect(
        user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
        database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
        host=str(configfile["database"]["host"]),
        port=str(configfile["database"]["port"])
    )
    query = """
            SELECT id, qt_id, title, ln_id, parent_nodes, q_dict, qt_age, qt_format, qt_order, repeatable_pattern, period_pattern, country_id, page_script, is_non_calculator, min_time, max_time, end_time, learning_content, time_created, time_last_edited, last_created_user_id
            FROM question_type  
            """
    records = await conn.fetch(query)
    question_type_list = [dict(record) for record in records]
    await conn.close()
    headers = ['id', 'qt_id', 'title', 'ln_id', 'parent_nodes', 'q_dict', 'qt_age', 'qt_format', 'qt_order', 'repeatable_pattern', 'period_pattern', 'country_id', 'page_script', 'is_non_calculator', 'min_time', 'max_time', 'end_time', 'learning_content', 'time_created', 'time_last_edited', 'last_created_user_id']
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames = headers, restval="", extrasaction='ignore', lineterminator= "\n")
    writer.writeheader()
    for record in question_type_list:
        writer.writerow(record)

    byte_output = BytesIO()
    byte_output.write(output.getvalue().encode('utf-8'))
    byte_output.seek(0)
    filename = "question_type.csv"

    return resp(
        content=byte_output.read(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
