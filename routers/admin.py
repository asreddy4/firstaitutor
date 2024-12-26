from fastapi import APIRouter, Request, Header, HTTPException, status, Request
from fastapi import Response as resp
from fastapi.responses import FileResponse, JSONResponse
import asyncpg
# import aiofiles
import os
import json
from utils.tools import find_country_code, save_user_token, find_user_id_by_token, connect_to_redis, count_records_by_user_id, \
    delete_user_tokens
from validations.admin import (Response, AdminRegistration, SuperAdminRegistration, CompleteRegistration, Login, Logout, DeleteAdmin)
import config
from datetime import datetime
import asyncio
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

@router.post("/super/admin/login", response_model=Response, summary="Super admin login.", tags=["admins"],
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
async def login_super_admin_user(login: Login):
    conn = await asyncpg.connect(
        user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
        database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
        host=str(configfile["database"]["host"]),
        port=str(configfile["database"]["port"])
    )
    query = """
           SELECT *
           FROM admins
           WHERE email = $1
       """
    record = await conn.fetchrow(query, login.email)
    try:
        if not record:
            return Response(status_code=status.HTTP_400_BAD_REQUEST, message="Incorrect email or password")

        if record["user_type"] != 'super_admin':
            return Response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="You do not have access to this section",
                data=None,
                detail=None,
            )
        user_id = record['id']
        if record["password"] != login.password:
            return Response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Incorrect email or password",
                data=None,
                detail=None
            )

        loop = asyncio.get_running_loop()
        token = await loop.run_in_executor(ThreadPoolExecutor(), save_user_token, user_id, False)
        last_login = "CURRENT_TIMESTAMP"
        query = f"UPDATE admins SET last_login = {last_login} WHERE email = $1"
        login_time = await conn.execute(query, login.email)
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


@router.post("/super/admin/creator", response_model=Response, summary="Create a new user by super_admin", tags=["admins"],
             responses={
                 200: {
                     "model": Response,
                     "description": "User successfully registered",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "The 'admin' user has been successfully registered",
                                 "data": {"email": "user@example.com", "fullname": "John Wick"},
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
async def super_admin_creator(register: SuperAdminRegistration, token: str = Header(...)):
    loop = asyncio.get_running_loop()
    user_id = await loop.run_in_executor(ThreadPoolExecutor(), find_user_id_by_token, token)
    if not user_id:
        return Response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid session ID"
        )
    try:
        conn = await asyncpg.connect(
            user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
            password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
            database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
            host=str(configfile["database"]["host"]),
            port=str(configfile["database"]["port"])
        )
        query = "SELECT * FROM admins WHERE id = $1"
        super_admin_record = await conn.fetchrow(query, int(user_id))
        if super_admin_record["user_type"] != 'super_admin':
            return Response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="You do not have permission to perform this action"
            )
        # Check if user already exists
        query = "SELECT id FROM admins WHERE email = $1"
        record = await conn.fetchrow(query, register.email)

        if record:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Email already exists",
                data=None,
                detail=None
            )

        # Insert new user
        query = """
            INSERT INTO admins (email, fullname, user_type, access_provider_email)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        """
        record = await conn.fetchrow(query, register.email, register.fullname, register.user_type, super_admin_record["email"])
        user_id = record['id']

        return Response(
            status_code=status.HTTP_200_OK,
            message=f"The '{register.user_type}' user has been registered successfully",
            data={"email": register.email, "fullname": register.fullname},
            detail=None
        )
    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create admin user: {str(e)}",
            data=None,
            detail=None
        )

    finally:
        await conn.close()

@router.post("/super/admin/logout", response_model=Response, summary="Logout", tags=["admins"],
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
async def logout_super_admin(token_request: Logout):
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

@router.get("/admins", response_model=Response, summary="Get all admin details", tags=["admins"],
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
                                        "fullname": "Example School",
                                        "email": "US",
                                        "access_provider_email": "NY",
                                        "whatsapp_number": "SCH12345",
                                        "telegram_number": "",
                                        "country": "India",
                                        "password": "secure_password",
                                        "user_type": "admin",
                                        "first_login": "",
                                        "last_login": ""
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
async def get_admin_details(token: str = Header(...)):
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

    # Optional: Check if user is super admin
    conn = await asyncpg.connect(
        user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
        database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
        host=str(configfile["database"]["host"]),
        port=str(configfile["database"]["port"])
    )
    try:
        query = "SELECT user_type FROM admins WHERE id = $1"
        user_type = await conn.fetchval(query, int(user_id))
        if user_type != 'super_admin':
            return Response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="You do not have access to this section",
                data=None,
                detail=None
            )

        # Fetch all admins from the database
        conn = await asyncpg.connect(
            user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
            password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
            database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
            host=str(configfile["database"]["host"]),
            port=str(configfile["database"]["port"])
        )
        query = """
                SELECT id, fullname, email, access_provider_email, whatsapp_number, telegram_number, country, password, user_type, first_login, last_login
                FROM admins
                """
        admins = await conn.fetch(query)
        if not admins:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="No admins data found",
                data=None,
                detail=None
            )
        admins_list = []
        for admin in admins:
            admins_data = {
                "id": admin['id'],
                "fullname": admin['fullname'],
                "email": admin['email'],
                "access_provider_email": admin['access_provider_email'] if admin['access_provider_email'] else None,
                "whatsapp_number": admin['whatsapp_number'] if admin['whatsapp_number'] else None,
                "telegram_number": admin['telegram_number'] if admin['telegram_number'] else None,
                "country": admin['country'] if admin['country'] else None,
                "password": admin['password'] if admin['password'] else None,
                "user_type": admin['user_type'] if admin['user_type'] else None,
                "first_login": str(admin['first_login']) if admin['first_login'] else None,
                "last_login": str(admin['last_login']) if admin['last_login'] else None
            }
            admins_list.append(admins_data)
        return Response(
            status_code=status.HTTP_200_OK,
            message="The request was successful",
            data=admins_list,
            detail=None
        )

    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to retrieve admins: {str(e)}",
            data=None,
            detail=None
        )
    finally:
        await conn.close()

@router.post("/delete/admin", response_model=Response, summary="Delete an existing admin by super admin",
             tags=["admins"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful request",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "admin user with email {email} deleted successfully",
                                 "data": {"id": 1},
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
async def delete_admin_by_super(admin_delete: DeleteAdmin, token: str = Header(...)):
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

    conn = await asyncpg.connect(
        user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
        database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
        host=str(configfile["database"]["host"]),
        port=str(configfile["database"]["port"])
    )
    try:
        query = "SELECT * FROM admins WHERE id = $1"
        admin_record = await conn.fetchrow(query, int(user_id))

        if admin_record["user_type"] != 'super_admin':
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="You do not have permission to perform this action",
                data=None,
                detail=None
            )
        if admin_record['id'] == admin_delete.id:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Deletion failed, admin can not be deleted by himself.",
                data=None,
                detail=None
            )
        query = """
                DELETE FROM admins
                WHERE id = $1
                RETURNING email
                """
        deleted_admin_email = await conn.fetchval(query, admin_delete.id)
        if deleted_admin_email:
            return Response(
                status_code=status.HTTP_200_OK,
                message=f"admin with ID {admin_delete.id} deleted successfully",
                data={"email": deleted_admin_email},
                detail=None
            )
        else:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="admin deletion failed",
                data=None,
                detail=None
            )
    except Exception as e:
        return Response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=f"Failed to delete admin: {str(e)}",
            data=None,
            detail=None
        )



@router.post("/admin/login", response_model=Response, summary="Admin login.", tags=["admins"],
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
async def login_admin_user(login: Login):
    conn = await asyncpg.connect(
        user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
        database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
        host=str(configfile["database"]["host"]),
        port=str(configfile["database"]["port"])
    )
    query = """
           SELECT *
           FROM admins
           WHERE email = $1
       """
    record = await conn.fetchrow(query, login.email)
    await conn.close()
    if not record:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, message="Incorrect email or password")

    if record["user_type"] != 'admin':
        return Response(
            status_code=status.HTTP_403_FORBIDDEN,
            message="You do not have access to this section",
            data=None,
            detail=None,
        )
    user_id = record['id']
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


@router.post("/admin/creator", response_model=Response, summary="Create a new user by admin", tags=["admins"],
             responses={
                 200: {
                     "model": Response,
                     "description": "User successfully registered",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "The 'question creator' user has been successfully registered",
                                 "data": {"email": "user@example.com", "fullname": "John Wick"},
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

async def admin_creator(register: AdminRegistration, token: str = Header(...)):
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
    query = "SELECT * FROM admins WHERE id = $1"
    admin_record = await conn.fetchrow(query, user_id)
    if admin_record["user_type"] != 'admin':
        return Response(
            status_code=status.HTTP_403_FORBIDDEN,
            message="You do not have permission to perform this action"
        )
    try:
        # Check if user already exists
        query = "SELECT id FROM admins WHERE email = $1"
        record = await conn.fetchrow(query, register.email)

        if record:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Email already exists",
                data=None,
                detail=None
            )

        # Insert new user
        query = """
                INSERT INTO admins (email, fullname, user_type, access_provider_email)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            """
        record = await conn.fetchrow(query, register.email, register.fullname, register.user_type, admin_record["email"])
        user_id = record['id']

        return Response(
            status_code=status.HTTP_200_OK,
            message=f"The '{register.user_type}' user has been registered successfully",
            data={"email": register.email, "fullname": register.fullname},
            detail=None
        )
    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create user: {str(e)}",
            data=None,
            detail=None
        )

    finally:
        await conn.close()

@router.post("/admin/logout", response_model=Response, summary="Logout", tags=["admins"],
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
async def logout_admin(token_request: Logout):
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

@router.post("/content_manager/login", response_model=Response, summary="content manager login.", tags=["admins"],
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
async def login_content_manager(login: Login):
    conn = await asyncpg.connect(
        user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
        database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
        host=str(configfile["database"]["host"]),
        port=str(configfile["database"]["port"])
    )
    query = """
           SELECT *
           FROM admins
           WHERE email = $1
       """
    record = await conn.fetchrow(query, login.email)
    await conn.close()
    if not record:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, message="Incorrect email or password")

    if record["user_type"] != 'content_manager':
        return Response(
            status_code=status.HTTP_403_FORBIDDEN,
            message="You do not have access to this section",
            data=None,
            detail=None,
        )
    user_id = record['id']
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

@router.post("/content_manager/logout", response_model=Response, summary="Logout", tags=["admins"],
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
async def logout_content_manager(token_request: Logout):
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

@router.post("/question_creator/login", response_model=Response, summary="question creator login.", tags=["admins"],
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
async def login_question_creator(login: Login):
    conn = await asyncpg.connect(
        user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
        database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
        host=str(configfile["database"]["host"]),
        port=str(configfile["database"]["port"])
    )
    query = """
           SELECT *
           FROM admins
           WHERE email = $1
       """
    record = await conn.fetchrow(query, login.email)
    await conn.close()
    if not record:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, message="Incorrect email or password")

    if record["user_type"] != 'question_creator':
        return Response(
            status_code=status.HTTP_403_FORBIDDEN,
            message="You do not have access to this section",
            data=None,
            detail=None,
        )
    user_id = record['id']
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

@router.post("/question_creator/logout", response_model=Response, summary="Logout", tags=["admins"],
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
async def logout_question_creator(token_request: Logout):
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

@router.post("/complete/registration", response_model=Response, summary="Complete user registration.", tags=["admins"],
             responses={
                 200: {
                     "model": Response,
                     "description": "User successfully registered",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "The user has been successfully registered",
                                 "data": None,
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

async def complete_registration(register: CompleteRegistration):
    conn = await asyncpg.connect(
        user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
        database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
        host=str(configfile["database"]["host"]),
        port=str(configfile["database"]["port"])
    )

    try:
        # Check if user already exists
        query = "SELECT id FROM admins WHERE email = $1"
        record = await conn.fetchrow(query, register.email)
        user_id = record['id']

        if record is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="You do not have access, Check your email. ",
                data=None,
                detail=None
            )

        # Update user details
        whatsapp = register.whatsapp_number if register.whatsapp_number is not None else 'null'
        telegram = register.telegram_number if register.telegram_number is not None else 'null'
        if whatsapp is None and telegram is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Both whatsapp and telegram can not be empty.",
                data=None,
                detail=None
            )
        query = """
                UPDATE admins 
                SET whatsapp_number = $1, telegram_number = $2, country = $3, password = $4 
                WHERE id = $5"""
        data = [whatsapp, telegram, register.country, register.password, user_id]
        record = await conn.execute(query, *data)

        return Response(
            status_code=status.HTTP_200_OK,
            message="The user has been successfully registered",
            data={"email": register.email},
            detail=None
        )
    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to complete user registration: {str(e)}",
            data=None,
            detail=None
        )

    finally:
        await conn.close()
