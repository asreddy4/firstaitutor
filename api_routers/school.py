from fastapi import APIRouter, Request, Header, HTTPException, status, Request
from fastapi import Response as resp
from fastapi.responses import FileResponse
import asyncpg
# import aiofiles
import os
import sys
import json
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

from api_validations.school import School, UpdateSchool, DeleteSchool

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

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'Utilities', 'schools_data.txt')


@router.get("/schools", response_model=Response, summary="Get all schools", tags=["Schools"],
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
                                        "name": "Example School",
                                        "country_code": "US",
                                        "county_state": "NY",
                                        "identification_code": "SCH12345"
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
async def get_schools(token: str = Header(...)):
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

    # Optional: Check if user is admin
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

    # Fetch all schools from the database
    conn = await asyncpg.connect(
        user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
        database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
        host=str(configfile["database"]["host"]),
        port=str(configfile["database"]["port"])
    )
    try:
        query = """
                SELECT id, name, country_code, county_state, identification_code
                FROM school
                """
        schools = await conn.fetch(query)

        # Handle case where no schools are found
        if not schools:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="No schools found",
                data=None,
                detail=None
            )

        # Prepare response with school data
        school_list = [{
            "id": school['id'],
            "name": school['name'],
            "country_code": school['country_code'],
            "county_state": school.get('county_state'),
            "identification_code": school['identification_code']
        } for school in schools]

        # Save schools data to a text file
        with open(DATA_FILE, 'w') as file:
            for school in school_list:
                file.write(f"ID: {school['id']}, Name: {school['name']}, Country Code: {school['country_code']}, "
                           f"County State: {school['county_state']}, Identification Code: {school['identification_code']}\n")

        return Response(
            status_code=status.HTTP_200_OK,
            message="The request was successful",
            data=school_list,
            detail=None
        )

    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to retrieve schools: {str(e)}",
            data=None,
            detail=None
        )
    finally:
        await conn.close()


@router.get("/schools/download", summary="Download all schools", tags=["Schools"])
async def download_schools(token: str = Header(...)):
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

    # Optional: Check if user is admin
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

    if not os.path.exists(DATA_FILE):
        return Response(
            status_code=status.HTTP_404_NOT_FOUND,
            message="File not found",
            data=None,
            detail=None
        )

    with open(DATA_FILE, 'r') as file:
        content = file.read()

    return resp(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=schools_data.txt"}
    )


@router.post("/schools/add", response_model=Response, summary="Create a new school", tags=["Schools"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful request",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "School with ID {school_id} created successfully",
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
async def create_school(school: School, token: str = Header(...)):
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
    name = school.name
    try:
        # country_code = await find_country_code(school.country)
        # city_code = await find_country_code(country_code, False, school.city)
        existing_id = await conn.fetchval(
            'SELECT id FROM school WHERE identification_code = $1', school.identification_code.lower().strip())
        if existing_id:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"This data has already been registered with ID {existing_id}",
                data=None,
                detail=None
            )
        query = """
                INSERT INTO school(name, country_code, county_state, identification_code)
                VALUES($1, $2, $3, $4)
                RETURNING id
                """
        school_id = await conn.fetchval(query, name.strip(), school.country_code, school.county_state,
                                        school.identification_code.lower().strip())
        await conn.close()

        if school_id:
            return Response(
                status_code=status.HTTP_200_OK,
                message=f"School with ID {school_id} created successfully",
                data=None,
                detail=None
            )
        else:
            return Response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Failed to create school",
                data=None,
                detail=None
            )

    except Exception as e:
        await conn.close()
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create school: {str(e)}"
        )


@router.post("/schools/edit", response_model=Response, summary="Update an existing school", tags=["Schools"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful request",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "School with ID {school_id} updated successfully",
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
async def update_school(school_update: UpdateSchool, token: str = Header(...)):
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
        # Check if the school exists
        existing_school = await conn.fetchrow('SELECT * FROM school WHERE id = $1',
                                              school_update.id)
        if existing_school["id"] is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="School not found",
                data=None,
                detail=None
            )

        # Update school information
        update_fields = []
        update_values = []
        if existing_school["name"] == school_update.name and existing_school["country_code"] == school_update.country and existing_school["county_state"] == school_update.county_state and existing_school["identification_code"] == school_update.identification_code.lower().strip():
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="No data has been changed, no editing is done",
                data=None,
                detail=None
            )
        if school_update.name:
            update_fields.append("name = $1")
            update_values.append(school_update.name.strip())
        if school_update.country:
            update_fields.append("country_code = $2")
            update_values.append(school_update.country)
        if school_update.county_state:
            update_fields.append("county_state = $3")
            update_values.append(school_update.county_state)
        if school_update.identification_code:
            if school_update.identification_code.lower().strip() != existing_school["identification_code"]:
                existing_id = await conn.fetchval(
                    'SELECT id FROM school WHERE identification_code = $1', school_update.identification_code.lower().strip())
                if existing_id:
                    return Response(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        message=f"This identification code has already been registered with ID {existing_id}",
                        data=None,
                        detail=None
                    )
            update_fields.append("identification_code = $4")
            update_values.append(school_update.identification_code.lower().strip())

        if not update_fields:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="No fields to update",
                data=None,
                detail=None
            )

        update_query = f"""
            UPDATE school
            SET {', '.join(update_fields)}
            WHERE id = ${len(update_values) + 1}
        """
        update_values.append(school_update.id)
        await conn.execute(update_query, *update_values)

        return Response(
            status_code=status.HTTP_200_OK,
            message=f"School with ID {school_update.id} updated successfully",
            data=None,
            detail=None
        )

    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to update school: {str(e)}",
            data=None,
            detail=None
        )
    finally:
        await conn.close()


@router.post("/schools/delete", response_model=Response, summary="Delete a school", tags=["Schools"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful request",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "School '{school_name}' with ID {school_id} deleted successfully",
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
async def delete_school(school_request: DeleteSchool, token: str = Header(...)):
    # Check user authentication based on token
    loop = asyncio.get_running_loop()
    user_id = await loop.run_in_executor(ThreadPoolExecutor(), find_user_id_by_token, token)
    if not user_id:
        return Response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid session ID"
        )

    # Optional: Check if user is admin
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

    # Delete the school from the database
    conn = await asyncpg.connect(
        user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
        database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
        host=str(configfile["database"]["host"]),
        port=str(configfile["database"]["port"])
    )
    try:
        delete_query = """
            DELETE FROM school
            WHERE id = $1
            RETURNING id, name
        """
        deleted_school = await conn.fetchrow(delete_query, school_request.school_id)
        if not deleted_school:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"School with ID {school_request.school_id} not found",
                data=None,
                detail=None
            )

        return Response(
            status_code=status.HTTP_200_OK,
            message=f"School '{deleted_school['name']}' with ID {deleted_school['id']} deleted successfully",
            data=None,
            detail=None
        )

    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to delete school: {str(e)}",
            data=None,
            detail=None
        )
    finally:
        await conn.close()

