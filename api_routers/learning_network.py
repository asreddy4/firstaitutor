from fastapi import APIRouter, Request, Header, HTTPException, status, Request
from fastapi import Response as resp
from fastapi.responses import FileResponse
import asyncpg
# import aiofiles
import os
import sys
import json
import config
from datetime import datetime
import asyncio
from fastapi.responses import JSONResponse
from concurrent.futures import ThreadPoolExecutor
from typing import Dict
from pydantic import BaseModel, ValidationError
import pytz
import yaml
import base64

from api_validations.learning_network import LearningNetwork, DeleteLearningNetwork, UpdateLearningNetwork

scriptDir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(scriptDir)
routersDir = (os.path.dirname(scriptDir)+"/validations")
sys.path.append(os.path.dirname(scriptDir))
sys.path.append(routersDir)

from api_utils.tools import find_country_code, save_user_token, find_user_id_by_token, connect_to_redis, count_records_by_user_id, delete_user_tokens
from api_validations.api_user import Response, Register, Login, Logout

#from forms import (Response, Subject, Register, Login, Logout, UpdateSubject, DeleteSubject, School, UpdateSchool,

configfile = {}
config_filepath = os.path.dirname(scriptDir)+"/configfile.yml"
if os.path.exists(config_filepath):
    with open(config_filepath, 'rt') as configFile:
        try:
            configfile = yaml.safe_load(configFile.read())
        except Exception as e:
            print("Check the ConfigFile "+str(e))

router = APIRouter()

@router.post("/learning_network/add", response_model=Response, summary="Create a new learning_network",
             tags=["learning_network"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful request",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "learning_network with ID {id} created successfully",
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
async def create_learning_network(ln_net: LearningNetwork, token: str = Header(...)):
    loop = asyncio.get_running_loop()
    user_id = await loop.run_in_executor(ThreadPoolExecutor(), find_user_id_by_token, token)
    if not user_id:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED, message="Invalid session ID")
    try:
        conn = await asyncpg.connect(
            user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
            password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
            database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
            host=str(configfile["database"]["host"]),
            port=str(configfile["database"]["port"])
        )
        existing_id_s = await conn.fetchval(
            'SELECT id FROM subject WHERE s_id = $1', ln_net.subject_id)
        if existing_id_s is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"This subject has not been registered with ID {existing_id_s if existing_id_s else ln_net.subject_id}",
                data=None,
                detail=None
            )
        # Check if a qualification with the same details already exists
        query = """SELECT id FROM learning_network WHERE ln_id = $1"""

        existing_id = await conn.fetchval(query, ln_net.ln_id)

        if existing_id:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"This learning_network data has already been registered with ID {existing_id}"
            )

        # Insert the new qualification record without q_id
        now = datetime.utcnow()
        insert_query = """
            INSERT INTO learning_network (
                ln_id, title, subject_id, parent_nodes, max_order, back_learning_level, is_subject_head_node, is_keynode, support_url, time_last_edited, last_created_user_id
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
            )
            RETURNING id
        """

        parent = ','.join(ln_net.parent_nodes) if ln_net.parent_nodes else None
        learning_network_id = await conn.fetchval(
            insert_query,
            ln_net.ln_id,
            ln_net.title,
            existing_id_s,
            parent,
            ln_net.max_order,
            ln_net.back_learning_level,
            ln_net.is_subject_head_node,
            ln_net.is_keynode,
            ln_net.support_url,
            now,
            int(user_id)
        )
        return Response(
            status_code=status.HTTP_200_OK,
            message=f"learning_network with ID {learning_network_id} created successfully",
            data=None,
            detail=None
        )
    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create qualification: {str(e)}"
        )
    finally:
        await conn.close()


@router.get("/learning_network", response_model=Response, summary="Get all learning_network",
            tags=["learning_network"],
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
                                        "q_id": "000001",
                                        "title": "Mathematics",
                                        "country_code": "GB",
                                        "subject_id": 123,
                                        "age": 25,
                                        "study_level": ["Key Stage 1", "Key Stage 2"],
                                        "var": ["Foundation", "Higher"],
                                        "org": ["Edexcel", "AQA"],
                                        "grade": ["A", "B"],
                                        "modules": ["Module 1", "Module 2"],
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
async def get_learning_network(token: str = Header(...)):
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
                SELECT id, ln_id, title, subject_id, parent_nodes, max_order, back_learning_level, is_subject_head_node, is_keynode, support_url, time_created, time_last_edited, last_created_user_id
                FROM learning_network
                """
        qualifications = await conn.fetch(query)

        # Prepare user emails for each qualification
        qualifications_list = []
        for qual in qualifications:
            timestamp0 = qual['time_created'].replace(tzinfo=pytz.UTC).timestamp()

            timestamp = qual['time_last_edited'].replace(tzinfo=pytz.UTC).timestamp()
            # Convert comma-separated strings to lists
            sub_name = await conn.fetchval("""SELECT name FROM subject WHERE id = $1""", qual['subject_id'])
            qualification_data = {
                "id": qual['id'],
                "ln_id": qual['ln_id'],
                "title": qual['title'],
                "subject_id": qual['subject_id'],
                "parent_nodes": qual['parent_nodes'].split(',') if qual['parent_nodes'] else [],
                "max_order": qual['max_order'],
                "back_learning_level": qual['back_learning_level'],
                "is_subject_head_node":qual['is_subject_head_node'],
                "is_keynode":qual['is_keynode'],
                "support_url": qual['support_url'],
                "time_created": timestamp0,
                "time_last_edited": timestamp
            }

            # Fetch user email
            user_query = "SELECT email FROM users WHERE id = $1"
            user_email = await conn.fetchval(user_query, int(qual['last_created_user_id']))
            qualification_data["last_edited_user_email"] = user_email

            qualifications_list.append(qualification_data)
        return Response(
            status_code=status.HTTP_200_OK,
            message="The request was successful",
            data=qualifications_list,
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

@router.post("/learning_network/delete", response_model=Response, summary="Delete an existing learning_network",
             tags=["learning_network"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful request",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "learning_network with ID {ln_id} deleted successfully",
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
async def delete_learning_network(qualification_delete: DeleteLearningNetwork, token: str = Header(...)):
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
                DELETE FROM learning_network
                WHERE id = $1
                RETURNING ln_id
                """
        deleted_qualification_id = await conn.fetchval(query, qualification_delete.id)

        if deleted_qualification_id:
            return Response(
                status_code=status.HTTP_200_OK,
                message=f"learning_network with ID {deleted_qualification_id} deleted successfully",
                data={"ln_id": deleted_qualification_id},
                detail=None
            )
        else:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="learning_network deletion failed",
                data=None,
                detail=None
            )
    except Exception as e:
        return Response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=f"Failed to delete learning_network: {str(e)}",
            data=None,
            detail=None
        )

@router.post("/learning_network/edit", response_model=Response, summary="Update an existing learning_network",
             tags=["learning_network"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful request",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "learning_network with ID {id} updated successfully",
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
async def update_learning_network(qualification_update: UpdateLearningNetwork, token: str = Header(...)):
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
        existing_qualification = await conn.fetchrow('SELECT * FROM learning_network WHERE id = $1',
                                                     qualification_update.id)
        if existing_qualification is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="learning_network not found",
                data=None,
                detail=None
            )
        existing_id_s = await conn.fetchval(
            'SELECT * FROM subject WHERE s_id = $1', qualification_update.subject_id)

        if existing_id_s is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"This subject has not been registered with ID {existing_id_s if existing_id_s else
                qualification_update.subject_id}",
                data=None,
                detail=None
            )
        # Prepare fields for update
        update_fields = []
        update_values = []
        parent = ','.join(qualification_update.parent_nodes) if qualification_update.parent_nodes else None
        if existing_qualification["ln_id"] == qualification_update.ln_id and existing_qualification["title"] == qualification_update.title and existing_qualification["subject_id"] == existing_id_s and existing_qualification["parent_nodes"] == parent and existing_qualification["max_order"] == qualification_update.max_order and existing_qualification["back_learning_level"] == qualification_update.back_learning_level and existing_qualification["is_subject_head_node"] == qualification_update.is_subject_head_node and existing_qualification["is_keynode"] == qualification_update.is_keynode and existing_qualification["support_url"] == qualification_update.support_url:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="No data has been changed, no editing is done",
                data=None,
                detail=None
            )
        if qualification_update.ln_id is not None:
            if existing_qualification['ln_id'] != qualification_update.ln_id:
                existing_id = await conn.fetchval(
                    'SELECT id FROM learning_network WHERE ln_id = $1',
                    qualification_update.ln_id)
                if existing_id:
                    return Response(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        message=f"This ln_id has already been registered with ID {existing_id}",
                        data=None,
                        detail=None
                    )
            update_fields.append("ln_id = $1")
            update_values.append(qualification_update.ln_id)
        if qualification_update.title is not None:
            update_fields.append("title = $2")
            update_values.append(qualification_update.title)
        if qualification_update.subject_id is not None:
            update_fields.append("subject_id = $3")
            update_values.append(existing_id_s)
        if qualification_update.parent_nodes is not None:
            update_fields.append("parent_nodes = $4")
            update_values.append(parent)
        if qualification_update.max_order is not None:
            update_fields.append("max_order = $5")
            update_values.append(qualification_update.max_order)
        if qualification_update.back_learning_level is not None:
            update_fields.append("back_learning_level = $6")
            update_values.append(qualification_update.back_learning_level)
        if qualification_update.is_subject_head_node is not None:
            update_fields.append("is_subject_head_node = $7")
            update_values.append(qualification_update.is_subject_head_node)
        if qualification_update.is_keynode is not None:
            update_fields.append("is_keynode = $8")
            update_values.append(qualification_update.is_keynode)
        if qualification_update.support_url is not None:
            update_fields.append("support_url = $9")
            update_values.append(qualification_update.support_url)


        if not update_fields:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="No fields to update",
                data=None,
                detail=None
            )
        now = datetime.utcnow()
        # Add fields for user ID and timestamp
        update_fields.extend(["time_last_edited = $10", "last_created_user_id = $11"])
        update_values.extend([now, int(user_id)])

        update_query = f"""
            UPDATE learning_network
            SET {', '.join(update_fields)}
            WHERE id = ${len(update_values) + 1}
        """
        update_values.append(qualification_update.id)
        await conn.execute(update_query, *update_values)

        return Response(
            status_code=status.HTTP_200_OK,
            message=f"learning_network with ID {qualification_update.id} updated successfully",
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