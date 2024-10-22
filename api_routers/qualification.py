from fastapi import APIRouter, Request, Header, HTTPException, status, Request
from fastapi import Response as resp
from fastapi.responses import FileResponse
import asyncpg
# import aiofiles
import os
import json
import sys
#from forms import (Response, Subject, Register, Login, Logout, UpdateSubject, DeleteSubject, School, UpdateSchool,
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

scriptDir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(scriptDir)
routersDir = (os.path.dirname(scriptDir)+"/validations")
sys.path.append(os.path.dirname(scriptDir))
sys.path.append(routersDir)

from api_utils.tools import find_country_code, save_user_token, find_user_id_by_token, connect_to_redis, count_records_by_user_id, delete_user_tokens
from api_validations.api_user import Response, Register, Login, Logout
from api_validations.qualification import QualificationRequest, DeleteQualification, QualificationUpdateRequest


configfile = {}
config_filepath = os.path.dirname(scriptDir)+"/configfile.yml"
if os.path.exists(config_filepath):
    with open(config_filepath, 'rt') as configFile:
        try:
            configfile = yaml.safe_load(configFile.read())
        except Exception as e:
            print("Check the ConfigFile "+str(e))

router = APIRouter()

@router.post("/qualifications/add", response_model=Response, summary="Create a new qualification",
             tags=["Qualifications"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful request",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "Qualification with ID {id} created successfully",
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
async def create_qualification(qualification: QualificationRequest, token: str = Header(...)):
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
            'SELECT id FROM subject WHERE id = $1', qualification.subject_id)
        if existing_id_s is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"This subject has not been registered with ID {existing_id_s if existing_id_s else qualification.subject_id}",
                data=None,
                detail=None
            )
        # Check if a qualification with the same details already exists
        query = """SELECT id FROM qualification WHERE title = $1 AND country_code = $2"""

        existing_id = await conn.fetchval(query, qualification.title.strip(), qualification.country_code)

        if existing_id:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"This qualification data has already been registered with ID {existing_id}"
            )

        # Insert the new qualification record without q_id
        now = datetime.utcnow()
        insert_query = """
            INSERT INTO qualification (
                title, country_code, subject_id, age, study_level, var, org, grade, modules, time_last_edited, last_created_user_id
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
            )
            RETURNING id
        """

        modules = ','.join(qualification.modules) if qualification.modules else ""
        study_level = ','.join(qualification.steps) if qualification.steps else ""

        qualification_id = await conn.fetchval(
            insert_query,
            qualification.title,
            qualification.country_code,
            qualification.subject_id,
            qualification.age,
            study_level,
            ','.join(qualification.var) if qualification.var else "",
            ','.join(qualification.org) if qualification.org else "",
            ','.join(qualification.grade) if qualification.grade else "",
            modules,
            now,
            int(user_id)
        )

        if qualification_id:
            # Update q_id with zero-padded format
            update_query = """
                UPDATE qualification
                SET q_id = LPAD(id::text, 6, '0')
                WHERE id = $1
            """
            await conn.execute(update_query, qualification_id)

            return Response(
                status_code=status.HTTP_200_OK,
                message=f"Qualification with ID {qualification_id} created successfully",
                data=None,
                detail=None
            )
        else:
            return Response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Failed to create qualification"
            )
    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create qualification: {str(e)}"
        )
    finally:
        await conn.close()


@router.post("/qualifications/delete", response_model=Response, summary="Delete an existing qualification",
             tags=["Qualifications"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful request",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "Qualification with ID {q_id} deleted successfully",
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
async def delete_qualification(qualification_delete: DeleteQualification, token: str = Header(...)):
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
                DELETE FROM qualification
                WHERE id = $1
                RETURNING q_id
                """
        deleted_qualification_id = await conn.fetchval(query, qualification_delete.id)

        if deleted_qualification_id:
            return Response(
                status_code=status.HTTP_200_OK,
                message=f"Qualification with ID {deleted_qualification_id} deleted successfully",
                data={"q_id": deleted_qualification_id},
                detail=None
            )
        else:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Qualification deletion failed",
                data=None,
                detail=None
            )
    except Exception as e:
        return Response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=f"Failed to delete qualification: {str(e)}",
            data=None,
            detail=None
        )


@router.post("/qualifications/edit", response_model=Response, summary="Update an existing qualification",
             tags=["Qualifications"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful request",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "Qualification with ID {id} updated successfully",
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
async def update_qualification(qualification_update: QualificationUpdateRequest, token: str = Header(...)):
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
        existing_qualification = await conn.fetchrow('SELECT * FROM qualification WHERE id = $1',
                                                     qualification_update.id)
        if existing_qualification is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Qualification not found",
                data=None,
                detail=None
            )
        existing_id_s = await conn.fetchval(
            'SELECT * FROM subject WHERE id = $1', qualification_update.subject_id)

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
        if existing_qualification["title"] == qualification_update.title and existing_qualification["country_code"] == qualification_update.country_code and existing_qualification["subject_id"] == qualification_update.subject_id and existing_qualification["age"] == qualification_update.age and existing_qualification["var"] == qualification_update.var and existing_qualification["org"] == qualification_update.org and existing_qualification["grade"] == qualification_update.grade and existing_qualification["study_level"] == qualification_update.steps and existing_qualification["modules"] == qualification_update.modules:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="No data has been changed, no editing is done",
                data=None,
                detail=None
            )
        if qualification_update.title is not None:
            update_fields.append("title = $1")
            update_values.append(qualification_update.title)
        if qualification_update.country_code is not None:
            if existing_qualification['country_code'] != qualification_update.country_code:
                existing_id = await conn.fetchval(
                    'SELECT id FROM qualification WHERE title = $1 AND country_code = $2',
                    qualification_update.title.strip(),
                    qualification_update.country_code)
                if existing_id:
                    return Response(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        message=f"This title and country code has already been registered with ID {existing_id}",
                        data=None,
                        detail=None
                    )
            update_fields.append("country_code = $2")
            update_values.append(qualification_update.country_code)
        if qualification_update.subject_id is not None:
            update_fields.append("subject_id = $3")
            update_values.append(qualification_update.subject_id)
        if qualification_update.age is not None:
            update_fields.append("age = $4")
            update_values.append(qualification_update.age)
        if qualification_update.var is not None:
            update_fields.append("var = $5")
            update_values.append(','.join(qualification_update.var))
        else:
            update_fields.append("var = $5")
            update_values.append("")
        if qualification_update.org is not None:
            update_fields.append("org = $6")
            update_values.append(','.join(qualification_update.org))
        else:
            update_fields.append("org = $6")
            update_values.append("")
        if qualification_update.steps is not None:
            update_fields.append("study_level = $7")
            update_values.append(','.join(qualification_update.steps))
        else:
            update_fields.append("study_level = $7")
            update_values.append("")
        if qualification_update.grade is not None:
            update_fields.append("grade = $8")
            update_values.append(','.join(qualification_update.grade))
        else:
            update_fields.append("grade = $8")
            update_values.append("")
        if qualification_update.modules and len(qualification_update.modules) > 0:
            update_fields.append("modules = $9")
            update_values.append(','.join(qualification_update.modules))
        else:
            update_fields.append("modules = $9")
            update_values.append("")

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
            UPDATE qualification
            SET {', '.join(update_fields)}
            WHERE id = ${len(update_values) + 1}
        """
        update_values.append(qualification_update.id)
        await conn.execute(update_query, *update_values)

        return Response(
            status_code=status.HTTP_200_OK,
            message=f"Qualification with ID {qualification_update.id} updated successfully",
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


@router.get("/qualifications", response_model=Response, summary="Get all qualifications",
            tags=["Qualifications"],
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
async def get_qualifications(token: str = Header(...)):
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
                SELECT id, q_id, title, country_code, subject_id, age, study_level, var, org, grade, modules, time_created, time_last_edited, last_created_user_id
                FROM qualification
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
                "q_id": qual['q_id'],
                "title": qual['title'],
                "country_code": qual['country_code'],
                "subject_name": sub_name,
                "age": qual['age'],
                "study_level": qual['study_level'].split(',') if qual['study_level'] else [],
                "var": qual['var'].split(',') if qual['var'] else [],
                "org": qual['org'].split(',') if qual['org'] else [],
                "grade": qual['grade'].split(',') if qual['grade'] else [],
                "modules": qual['modules'].split(',') if qual['modules'] else [],
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


