from fastapi import APIRouter, Request, Header, HTTPException, status, Request
from fastapi import Response as resp
from fastapi.responses import FileResponse
import asyncpg
# import aiofiles
import os
import sys
import json
#from validations.forms import (Response, Subject, Register, Login, Logout, UpdateSubject, DeleteSubject, School, UpdateSchool,
#                   DeleteSchool, QualificationRequest, QualificationUpdateRequest, DeleteQualification, #LearningNetwork,DeleteLearningNetwork,UpdateLearningNetwork)
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

from api_validations.subject import Subject, DeleteSubject, UpdateSubject

scriptDir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(scriptDir)
routersDir = (os.path.dirname(scriptDir)+"/validations")
sys.path.append(os.path.dirname(scriptDir))
sys.path.append(routersDir)

from api_utils.tools import find_country_code, save_user_token, find_user_id_by_token, connect_to_redis, count_records_by_user_id, delete_user_tokens
from api_validations.api_user import Response, Register, Login, Logout


configfile = {}
config_filepath = os.path.dirname(scriptDir)+"/configfile.yml"
if os.path.exists(config_filepath):
    with open(config_filepath, 'rt') as configFile:
        try:
            configfile = yaml.safe_load(configFile.read())
        except Exception as e:
            print("Check the ConfigFile "+str(e))

router = APIRouter()

@router.get("/subjects", response_model=Response, summary="Get all subjects", tags=["Subjects"],
            responses={
                200: {
                    "model": Response,
                    "description": "Successful request",
                    "content": {
                        "application/json": {
                            "example": {
                                "status_code": 200,
                                "message": "The request was successful",
                                "data": [{"id": "1", "name": "Math"}, {"id": "2", "name": "Science"}],
                                "detail": None
                            }
                        }
                    }
                },
                422: {
                    "model": Response,
                    "description": "Validation error (e.g., invalid session ID)",
                    "content": {
                        "application/json": {
                            "example": {
                                "status_code": 422,
                                "message": "Validation error",
                                "data": None,
                                "detail": [
                                    {"loc": ["header", "token"], "msg": "Invalid session ID", "type": "value_error"}]
                            }
                        }
                    }
                }
            })
async def get_subjects(token: str = Header(...)):
    # Find user ID from token
    loop = asyncio.get_running_loop()
    user_id = await loop.run_in_executor(ThreadPoolExecutor(), find_user_id_by_token, token)

    if not user_id:
        return Response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Invalid session ID",
            data=None,
            detail=None
        )

    # Check user access
    conn = await asyncpg.connect(
        user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
        database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
        host=str(configfile["database"]["host"]),
        port=str(configfile["database"]["port"])
    )
    query = """
            SELECT *
            FROM users
            WHERE id = $1
        """
    user = await conn.fetchrow(query, int(user_id))
    await conn.close()

    if user["is_admin"] is False:
        return Response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="You do not have access to this section",
            data=None,
            detail=None
        )

    # Get subjects
    conn = await asyncpg.connect(
        user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
        database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
        host=str(configfile["database"]["host"]),
        port=str(configfile["database"]["port"])
    )
    try:
        query = """
                SELECT id, name, s_id
                FROM subject
                """
        subjects = await conn.fetch(query)
    finally:
        await conn.close()

    if not subjects:
        return Response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="No subjects found",
            data=None,
            detail=None
        )

    subject_list = [{"id": str(subject['id']), "s_id": str(subject['s_id']), "name": subject['name'].capitalize()} for subject in
                    subjects]
    return Response(
        status_code=status.HTTP_200_OK,
        message="The request was successful",
        data=subject_list,
        detail=None
    )


@router.post("/subjects/add", response_model=Response, summary="Create a new subject", tags=["Subjects"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful request",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "Your data has been correctly registered in the database",
                                 "data": None,
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
                                     {"loc": [], "msg": "You do not have access to this section",
                                      "type": "access_error"}
                                 ]
                             }
                         }
                     }
                 }
             })
async def create_subject(subject: Subject, token: str = Header(...)):
    loop = asyncio.get_running_loop()
    user_id = await loop.run_in_executor(ThreadPoolExecutor(), find_user_id_by_token, token)
    if not user_id:
        return Response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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
    query = """
            SELECT *
            FROM users
            WHERE id = $1
        """
    user = await conn.fetchrow(query, int(user_id))
    await conn.close()

    if user is None or user.get("is_admin") is False:
        return Response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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

    name = subject.name.lower()
    try:
        existing_id = await conn.fetchval(
            'SELECT id FROM subject WHERE name = $1', name.strip())
        if existing_id:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"This data has already been registered with subject name {name.strip()}",
                data=None,
                detail=None
            )
        existing_S_id = await conn.fetchval(
            'SELECT id FROM subject WHERE s_id = $1', subject.s_id)
        if existing_S_id:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"This data has already been registered with subject id {subject.s_id}",
                data=None,
                detail=None
            )
        new_id = await conn.fetchval(
            'INSERT INTO subject(name,s_id) VALUES($1,$2) RETURNING id', name.strip(), subject.s_id.strip())
        return Response(
            status_code=status.HTTP_200_OK,
            message="Your data has been correctly registered in the database",
            data=None,
            detail=None
        )

    finally:
        await conn.close()


@router.post("/subjects/delete", response_model=Response, summary="Delete an existing subject", tags=["Subjects"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful request",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "Subject with ID {subject_id} ({subject_name}) deleted successfully",
                                 "data": {"subject_id": 1, "subject_name": "Mathematics"},
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
async def delete_subject(subject_delete: DeleteSubject, token: str = Header(...)):
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

        # Delete the subject from the database
        query = """
                DELETE FROM subject
                WHERE id = $1
                RETURNING name
                """
        deleted_subject_name = await conn.fetchval(query, subject_delete.subject_id)

        if deleted_subject_name:
            return Response(
                status_code=status.HTTP_200_OK,
                message=f"Subject with ID {subject_delete.subject_id} ({deleted_subject_name}) deleted successfully",
                data={"subject_id": subject_delete.subject_id, "subject_name": deleted_subject_name},
                detail=None
            )
        else:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Subject deletion failed",
                data=None,
                detail=None
            )
    except Exception as e:
        return Response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="The subject cannot be deleted.",
            # message=f"Failed to delete subject: {str(e)}",
            data=None,
            detail=None
        )
    finally:
        await conn.close()


@router.post("/subjects/edit", response_model=Response, summary="Edit an existing subject", tags=["Subjects"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful request",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "Subject with ID {subject_id} updated successfully",
                                 "data": None,
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
async def edit_subject(subject_update: UpdateSubject, token: str = Header(...)):
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

        # Update the subject in the database
        existing_id = await conn.fetchrow(
            'SELECT * FROM subject WHERE id = $1', subject_update.subject_id)
        if existing_id is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Subject not found",
                data=None,
                detail=None
            )
        name = subject_update.new_name.lower()
        if name.strip() == existing_id["name"] and subject_update.s_id == existing_id["s_id"]:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="No data has been changed, no editing is done",
                data=None,
                detail=None
            )
        if name.strip() != existing_id["name"]:
            existing_name = await conn.fetchval(
                'SELECT id FROM subject WHERE name = $1', name.strip())
            if existing_name:
                return Response(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    message=f"This data has already been registered with ID {existing_name}",
                    data=None,
                    detail=None
                )
        if subject_update.s_id != existing_id["s_id"]:
            existing_S_id = await conn.fetchval(
                'SELECT id FROM subject WHERE s_id = $1', subject_update.s_id)
            if existing_S_id:
                return Response(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    message=f"This data has already been registered with ID {existing_S_id}",
                    data=None,
                    detail=None
                )
        update_fields = []
        update_values = []
        if subject_update.new_name:
            update_fields.append("name = $1")
            update_values.append(name.strip())
        if subject_update.s_id:
            update_fields.append("s_id = $2")
            update_values.append(subject_update.s_id.strip())
        try:
            update_query = f"""
                        UPDATE subject
                        SET {', '.join(update_fields)}
                        WHERE id = ${len(update_values) + 1}
                    """
            update_values.append(subject_update.subject_id)
            await conn.execute(update_query, *update_values)
            return Response(
                status_code=status.HTTP_200_OK,
                message=f"Subject with ID {subject_update.subject_id} updated successfully",
                data=None,
                detail=None
            )
        except Exception as e:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Subject update failed",
                data=None,
                detail=None
            )
    except Exception as e:
        return Response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=f"Failed to update subject: {str(e)}",
            data=None,
            detail=None
        )
    finally:
        await conn.close()

