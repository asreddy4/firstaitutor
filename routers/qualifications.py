import sys
from fastapi import APIRouter, Request, Header, HTTPException, status, Request, UploadFile
from fastapi import Response as resp
from fastapi.responses import FileResponse
import asyncpg
# import aiofiles
import os
import json
from utils.tools import find_country_code, save_user_token, find_user_id_by_token, connect_to_redis, count_records_by_user_id, \
    delete_user_tokens
#from forms import (Response, Subject, Register, Login, Logout, UpdateSubject, DeleteSubject, School, UpdateSchool,
#                   DeleteSchool, QualificationRequest, QualificationUpdateRequest, DeleteQualification, #LearningNetwork,DeleteLearningNetwork,UpdateLearningNetwork)
from validations.qualifications import (Response, QualificationRequest, QualificationUpdateRequest, DeleteQualification)
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

scriptDir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
qualification_options = scriptDir +'/fait_back_res/backend_data_options/qualification_options.json'

def read_qualification_json(file_path : str):
    with open(file_path, 'r') as file:
        return json.load(file)

router = APIRouter()

@router.post("/qualifications/add", response_model=Response, summary="Create a new qualification",
             tags=["qualifications"],
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
        existing_qual_id = await conn.fetchval(
            'SELECT id FROM qualification WHERE qual_id = $1', qualification.qual_id
        )
        if existing_qual_id:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"This qualification id '{qualification.qual_id}' already exists in the database.",
                data=None,
                detail=None
            )
        existing_subject = await conn.fetchrow(
            'SELECT * FROM subject WHERE name = $1', qualification.subject_name)
        if existing_subject is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"This subject name '{qualification.subject_name}' not exists in the database.",
                data=None,
                detail=None
            )
        # Check if a qualification with the same details already exists
        query = """SELECT id FROM qualification WHERE title = $1 AND country_code = $2"""
        existing_id = await conn.fetchval(query, qualification.title, qualification.country_code)

        if existing_id:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"This qualification title '{qualification.title}' in country '{qualification.country_code}' already exists in database."
            )

        # Insert the new qualification record without qual_id
        now = datetime.utcnow()
        insert_query = """
            INSERT INTO qualification (
                qual_id, title, country_code, subject_id, age, study_level, var, org, grade, modules, time_last_edited, last_created_user_id
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
            )
            RETURNING id
        """

        qualification_id = await conn.fetchval(
            insert_query,
            qualification.qual_id,
            qualification.title,
            qualification.country_code,
            existing_subject['subject_id'],
            qualification.age,
            json.dumps(qualification.study_level),
            json.dumps(qualification.var),
            json.dumps(qualification.org),
            json.dumps(qualification.grade),
            json.dumps(qualification.modules),
            now,
            int(user_id)
        )

        # if qualification_id:
        #     # Update qual_id with zero-padded format
        #     update_query = """
        #         UPDATE qualification
        #         SET qual_id = LPAD(id::text, 6, '0')
        #         WHERE id = $1
        #     """
        #     await conn.execute(update_query, qualification_id)
        #
        #     return Response(
        #         status_code=status.HTTP_200_OK,
        #         message=f"Qualification with ID {qualification_id} created successfully",
        #         data=None,
        #         detail=None
        #     )
        # else:
        #     return Response(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         message="Failed to create qualification"
        #     )

        return Response(
                status_code=status.HTTP_200_OK,
                message=f"Qualification with ID {qualification_id} created successfully",
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


@router.post("/qualifications/delete", response_model=Response, summary="Delete an existing qualification",
             tags=["qualifications"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful request",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "Qualification with ID {qual_id} deleted successfully",
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
                RETURNING qual_id
                """
        deleted_qualification_id = await conn.fetchval(query, qualification_delete.id)

        if deleted_qualification_id:
            return Response(
                status_code=status.HTTP_200_OK,
                message=f"Qualification with ID {deleted_qualification_id} deleted successfully",
                data={"qual_id": deleted_qualification_id},
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
             tags=["qualifications"],
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
        existing_subject = await conn.fetchrow(
            'SELECT * FROM subject WHERE name = $1', qualification_update.subject_name)
        if existing_subject is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"The subject name '{qualification_update.subject_name}' not exists in database.",
                data=None,
                detail=None
            )

        # query = """SELECT id FROM qualification WHERE title = $1 AND country_code = $2"""
        # existing_id = await conn.fetchval(query, qualification_update.title, qualification_update.country_code)
        # if existing_id:
        #     return Response(
        #         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        #         message=f"This qualification title '{qualification_update.title}' in country '{qualification_update.country_code}' already exists in database."
        #     )
        # Prepare fields for update
        update_fields = []
        update_values = []
        if (existing_qualification['qual_id'] == qualification_update.qual_id and existing_qualification["title"] == qualification_update.title and
                existing_qualification["country_code"] == qualification_update.country_code and existing_qualification["subject_id"] == existing_subject['subject_id'] and
                existing_qualification["age"] == qualification_update.age and existing_qualification["var"] == json.dumps(qualification_update.var) and
                existing_qualification["org"] == json.dumps(qualification_update.org) and existing_qualification["grade"] == json.dumps(qualification_update.grade) and
                existing_qualification["study_level"] == json.dumps(qualification_update.study_level) and existing_qualification["modules"] == json.dumps(qualification_update.modules)):
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="No data has been changed, no editing is done",
                data=None,
                detail=None
            )
        if qualification_update.qual_id is not None:
            if existing_qualification['qual_id'] != qualification_update.qual_id:
                existing_id = await conn.fetchval(
                    'SELECT * FROM qualification WHERE qual_id = $1',
                    qualification_update.qual_id)
                if existing_id:
                    return Response(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        message=f"This qualification id '{qualification_update.qual_id}' already exists in database.",
                        data=None,
                        detail=None
                    )
            update_fields.append("qual_id = $1")
            update_values.append(qualification_update.qual_id)
        if qualification_update.title is not None:
            update_fields.append("title = $2")
            update_values.append(qualification_update.title)
        if qualification_update.country_code is not None:
            if existing_qualification['country_code'] != qualification_update.country_code:
                existing_id = await conn.fetchval(
                    'SELECT id FROM qualification WHERE title = $1 AND country_code = $2',
                    qualification_update.title, qualification_update.country_code)
                if existing_id:
                    return Response(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        message=f"This qualification title '{qualification_update.title}' and country code '{qualification_update.country_code}' has already been registered with ID {existing_id}",
                        data=None,
                        detail=None
                    )
            update_fields.append("country_code = $3")
            update_values.append(qualification_update.country_code)
        if qualification_update.subject_name is not None:
            update_fields.append("subject_id = $4")
            update_values.append(existing_subject['subject_id'])
        if qualification_update.age is not None:
            update_fields.append("age = $5")
            update_values.append(qualification_update.age)
        if qualification_update.var is not None:
            update_fields.append("var = $6")
            update_values.append(json.dumps(qualification_update.var))
        else:
            update_fields.append("var = $6")
            update_values.append(json.dumps(qualification_update.var))
        if qualification_update.org is not None:
            update_fields.append("org = $7")
            update_values.append(json.dumps(qualification_update.org))
        else:
            update_fields.append("org = $7")
            update_values.append(json.dumps(qualification_update.org))
        if qualification_update.study_level is not None:
            update_fields.append("study_level = $8")
            update_values.append(json.dumps(qualification_update.study_level))
        else:
            update_fields.append("study_level = $8")
            update_values.append(json.dumps(qualification_update.study_level))
        if qualification_update.grade is not None:
            update_fields.append("grade = $9")
            update_values.append(json.dumps(qualification_update.grade))
        else:
            update_fields.append("grade = $9")
            update_values.append(json.dumps(qualification_update.grade))
        if qualification_update.modules is not None:
            update_fields.append("modules = $10")
            update_values.append(json.dumps(qualification_update.modules))
        else:
            update_fields.append("modules = $10")
            update_values.append(json.dumps(qualification_update.modules))
        if not update_fields:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="No fields to update",
                data=None,
                detail=None
            )
        now = datetime.utcnow()
        # Add fields for user ID and timestamp
        update_fields.extend(["time_last_edited = $11", "last_created_user_id = $12"])
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
            message=f"Qualification with ID '{qualification_update.qual_id}' updated successfully",
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
            tags=["qualifications"],
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
                                        "qual_id": "000001",
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
                SELECT id, qual_id, title, country_code, subject_id, age, study_level, var, org, grade, modules, time_created, time_last_edited, last_created_user_id
                FROM qualification
                """
        qualifications = await conn.fetch(query)
        # Prepare user emails for each qualification
        qualifications_list = []
        for qual in qualifications:
            timestamp0 = qual['time_created'].replace(tzinfo=pytz.UTC).timestamp()

            timestamp = qual['time_last_edited'].replace(tzinfo=pytz.UTC).timestamp()
            # Convert comma-separated strings to lists
            sub_name = await conn.fetchval("""SELECT name FROM subject WHERE subject_id = $1""", qual['subject_id'])
            qualification_data = {
                "id": qual['id'],
                "qual_id": qual['qual_id'],
                "title": qual['title'],
                "country_code": qual['country_code'],
                "subject_name": sub_name if sub_name  else None,
                "age": qual['age'],
                "study_level": json.loads(qual['study_level']),
                "var": json.loads(qual['var']),
                "org": json.loads(qual['org']),
                "grade": json.loads(qual['grade']),
                "modules": json.loads(qual['modules']),
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

@router.get("/qualifications/download", summary="Download all qualifications", tags=["qualifications"])
async def download_qualifications(token: str = Header(...)):
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
                SELECT id, qual_id, title, country_code, subject_id, age, study_level, var, org, grade, modules, time_created, time_last_edited, last_created_user_id
                FROM qualification  
                """
        records = await conn.fetch(query)
        qualifications_list = [dict(record) for record in records]
        await conn.close()
        headers = ['id', 'qual_id', 'title', 'country_code', 'subject_id', 'age', 'study_level', 'var', 'org', 'grade', 'modules', 'time_created', 'time_last_edited', 'last_created_user_id']
        scriptDir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = scriptDir + f'/fait_back_res/backend_data_rep/qualification_download_{timestamp}.csv'
        with open(file_path, 'w', newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers, restval="", extrasaction='ignore', lineterminator="\n")
            writer.writeheader()
            for record in qualifications_list:
                writer.writerow(record)

        return Response(
            status_code=status.HTTP_200_OK,
            message=f"File created successfully.",
            data={'filename': f'qualification_download_{timestamp}.csv'},
            detail=None
        )
    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to download qualification: {str(e)}",
            data=None,
            detail=None
        )

@router.post("/qualifications/upload", summary="Upload qualifications", tags=["qualifications"])
async def upload_qualifications(file: UploadFile, token: str = Header(...)):
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
    existing_qual_ids = await conn.fetch("SELECT qual_id from qualification")
    existing_qual_records = {record['qual_id'] for record in existing_qual_ids}
    existing_subject_ids = await conn.fetch("SELECT subject_id from subject")
    existing_subject_records = {record['subject_id'] for record in existing_subject_ids}

    try:
        content = await file.read()
        csv_data = content.decode('utf-8').splitlines()
        reader = csv.DictReader(csv_data)
        new_qualification_ids = []
        unsuccessful_list = []
        for row in reader:
            validation = True
            qualification_options_dict = read_qualification_json(qualification_options)
            allowed_var = qualification_options_dict['qualification_var']
            allowed_org = qualification_options_dict['qualification_org']
            allowed_study_level = qualification_options_dict['study_levels']
            allowed_grade = qualification_options_dict['qualification_grades']
            allowed_module = qualification_options_dict['qualification_modules']
            try:
                qual_id = row['qual_id']
                title = row['title']
                country_code = row['country_code']
                var = row['var']
                org = row['org']
                study_level = row['study_level']
                grade = row['grade']
                module = row['modules']
                if not qual_id.isdigit():
                    validation = False
                if title is None:
                    validation = False
                if len(country_code) != 2 or not country_code.isupper():
                    validation = False
                if var is not None:
                    var_field = json.loads(var)
                    for item in var_field:
                        if item not in allowed_var:
                            validation = False
                if org is not None:
                    org_field = json.loads(org)
                    for item in org_field:
                        if item not in allowed_org:
                            validation = False
                if study_level is not None:
                    study_level_field = json.loads(study_level)
                    for item in study_level_field:
                        if item not in allowed_study_level:
                            validation = False
                if grade is not None:
                    grade_field = json.loads(grade)
                    for item in grade_field:
                        if item not in allowed_grade:
                            validation = False
                if module is not None:
                    module_field = json.loads(module)
                    for item in module_field:
                        if item not in allowed_module:
                            validation = False

            except Exception as e:
                validation = False

            conn = await asyncpg.connect(
                user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
                password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
                database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
                host=str(configfile["database"]["host"]),
                port=str(configfile["database"]["port"])
            )
            existing_id = await conn.fetchval(
                'SELECT id FROM qualification WHERE title = $1 AND country_code = $2',
                row['title'], row['country_code'])

            if row['subject_id'] in existing_subject_records and row['qual_id'] not in existing_qual_records and existing_id is None and validation == True:

                now = datetime.utcnow()
                insert_query = """
                            INSERT INTO qualification (
                                qual_id, title, country_code, subject_id, age, study_level, var, org, grade, modules, time_last_edited, last_created_user_id
                            ) VALUES (
                                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
                            )
                            RETURNING qual_id
                        """
                modules = row['modules']
                study_level = row['study_level']

                qualification_id = await conn.fetchval(
                    insert_query,
                    qual_id.zfill(6),
                    row['title'],
                    row['country_code'],
                    row['subject_id'],
                    int(row['age']),
                    study_level,
                    row['var'],
                    row['org'],
                    row['grade'],
                    modules,
                    now,
                    int(user_id)
                )

                # if qualification_id:
                #     # Update qual_id with zero-padded format
                #     update_query = """
                #         UPDATE qualification
                #         SET qual_id = LPAD(id::text, 6, '0')
                #         WHERE id = $1
                #     """
                #     await conn.execute(update_query, qualification_id)
                new_qualification_ids.append(qualification_id)
            else:
                unsuccessful_list.append(row['qual_id'].zfill(6))
        return Response(
            status_code=status.HTTP_200_OK,
            message=f"Qualification with IDs '{new_qualification_ids}' created successfully and Unsuccessful IDs are '{unsuccessful_list}'",
            data=None,
            detail=None
        )
    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create qualification IDs: {str(e)}"
        )

