from fastapi import APIRouter, Request, Header, HTTPException, status, Request
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
from validations.user import (Response, Register, Login, Logout)
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
configfile = {}
config_filepath = os.path.dirname(scriptDir)+"/configfile.yml"
if os.path.exists(config_filepath):
    with open(config_filepath, 'rt') as configFile:
        try:
            configfile = yaml.safe_load(configFile.read())
        except Exception as e:
            print("Check the ConfigFile "+str(e))

router = APIRouter()


@router.post("/user/admin/login", response_model=Response, summary="Login to the application", tags=["user"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful login",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "Login successful",
                                 "data": {"token": "your_generated_token_here"},
                                 "detail": None
                             }
                         }
                     }
                 },
                 422: {
                     "model": Response,
                     "description": "Validation error (e.g., incorrect email format)",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 422,
                                 "message": "Validation error",
                                 "data": None,
                                 "detail": [{"loc": ["body", "email"], "msg": "Invalid email address",
                                             "type": "value_error.email"}]
                             }
                         }
                     }
                 }
             })
async def login_user(login: Login):
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
           WHERE email = $1
       """
    record = await conn.fetchrow(query, login.email)
    await conn.close()
    try:
        if not record:
            return Response(status_code=status.HTTP_400_BAD_REQUEST, message="Incorrect email or password")

        if record["is_admin"] is False:
            return Response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="You do not have access to this section",
                data=None,
                detail=None,
            )
        user_id = record['id']
        # loop = asyncio.get_running_loop()
        # count = await loop.run_in_executor(ThreadPoolExecutor(), count_records_by_user_id, user_id)
        # if count >= 3:
        #     return Response(
        #         status_code=status.HTTP_300_MULTIPLE_CHOICES,
        #         message="You are logged in on 3 devices at the same time and you cannot login",
        #         data=None,
        #         detail=None
        #     )

        if record["password"] != login.password:
            return Response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Incorrect email or password",
                data=None,
                detail=None
            )

        loop = asyncio.get_running_loop()
        token = await loop.run_in_executor(ThreadPoolExecutor(), save_user_token, user_id, False)

        return Response(
            status_code=status.HTTP_200_OK,
            message="Login successful",
            data={"token": token},
            detail=None
        )
    except Exception as e:
        await conn.close()
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to login: {str(e)}"
        )

@router.post("/user/logout", response_model=Response, summary="Logout", tags=["user"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful logout",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "Token and its related keys have been invalidated.",
                                 "data": None,
                                 "detail": None
                             }
                         }
                     }
                 },
                 422: {
                     "model": Response,
                     "description": "Validation error (e.g., token format is incorrect)",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 422,
                                 "message": "Validation error",
                                 "data": None,
                                 "detail": [
                                     {"loc": ["body", "token"], "msg": "Invalid token format", "type": "value_error"}]
                             }
                         }
                     }
                 }
             })
async def logout_user(token_request: Logout):
    token = token_request.token

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(ThreadPoolExecutor(), delete_user_tokens, token)

    if result is False:
        return Response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Invalid token or token not found",
            data=None,
            detail=None
        )

    return Response(
        status_code=status.HTTP_200_OK,
        message=f"Token {token} and its related keys have been invalidated.",
        data=None,
        detail=None
    )


@router.post("/user/register", response_model=Response, summary="Create a new user", tags=["user"],
             responses={
                 200: {
                     "model": Response,
                     "description": "User successfully registered",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "The user has been successfully registered",
                                 "data": {"token": "your_generated_token_here"},
                                 "detail": None
                             }
                         }
                     }
                 },
                 422: {
                     "model": Response,
                     "description": "Validation error or conflict (e.g., user with this email already exists)",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 422,
                                 "message": "Validation error",
                                 "data": None,
                                 "detail": [{"loc": ["body", "email"], "msg": "Email already exists",
                                             "type": "value_error.email"}]
                             }
                         }
                     }
                 }
             })
async def register_user(register: Register):
    conn = await asyncpg.connect(
        user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
        database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
        host=str(configfile["database"]["host"]),
        port=str(configfile["database"]["port"])
    )

    try:
        # Check if user already exists
        query = "SELECT id FROM users WHERE email = $1"
        record = await conn.fetchrow(query, register.email)

        if record:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Email already exists",
                data=None,
                detail=None
            )

        # Insert new user
        country_code = await find_country_code(register.country_name)
        city_code = await find_country_code(country_code, False, register.country_name)

        is_admin = register.user_type == "admin"
        user_type = 1 if is_admin else 2

        query = """
            INSERT INTO users (email, phone, is_admin, date_of_birth, country_code, city_code, user_type, password)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """
        record = await conn.fetchrow(query,
                                     register.email, register.phone, is_admin, register.date_of_birth,
                                     country_code, city_code[0],
                                     user_type, register.password)
        user_id = record['id']

        # Generate token if the user is admin
        loop = asyncio.get_running_loop()
        token = await loop.run_in_executor(ThreadPoolExecutor(), save_user_token, user_id, is_admin)

        response_data = {
            "status_code": status.HTTP_200_OK,
            "message": "The user has been successfully registered",
            "data": {"token": token},
            "detail": None
        }
        return Response(
            status_code=status.HTTP_200_OK,
            message="The user has been successfully registered",
            data={"token": token},
            detail=None
        )

    finally:
        await conn.close()
