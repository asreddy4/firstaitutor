from fileinput import filename

from fastapi import APIRouter, Request, Header, HTTPException, status, Request, UploadFile, Query, Path
from fastapi import Response as resp
import asyncpg
import os

from pandas.compat.numpy.function import validate_argmax

from utils.tools import find_country_code, save_user_token, find_user_id_by_token, connect_to_redis, count_records_by_user_id, \
    delete_user_tokens
from validations.backend_options import Response
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


@router.get("/backend_options", summary="Convert json file for frontend", tags=["backend_options"])
async def convert_backend_options(name: str = Query(...,example="qualification_options", description="filename"), token: str = Header(...)):
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
        home_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        qualification_options = home_dir + f'/fait_back_res/backend_data_options/{name}.json'

        with open(qualification_options, 'r') as file:
            qualification_options_dict = json.load(file)
        json_data = {}
        for i in qualification_options_dict:
            json_data[i] = []
            for j in qualification_options_dict[i]:
                json_data[i].append(
                    {
                        "label": j,
                        "value": j
                    }
                )
        return Response(
            status_code=status.HTTP_200_OK,
            message=f"File {name} converted successfully.",
            data=json_data,
            detail=None
        )
    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to convert '{name}': {str(e)}",
            data=None,
            detail=None
        )


@router.get("/backend_options/{name}/json_file", summary="Fetch json file", tags=["backend_options"])
async def get_backend_options(name: str = Path(...,example="qualification_options", description="filename"), token: str = Header(...)):
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
        home_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        file_name = home_dir + f'/fait_back_res/backend_data_options/{name}.json'

        with open(file_name, 'r') as file:
            json_data = json.load(file)

        return Response(
            status_code=status.HTTP_200_OK,
            message=f"File {name} successfully fetched.",
            data=json_data,
            detail=None
        )
    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch '{name}': {str(e)}",
            data=None,
            detail=None
        )

@router.get("/frontend_res/{name}/images", summary="Fetch image source files", tags=["backend_options"])
async def get_image_source_files(name: str = Path(...,example="image_source", description="folder name"), token: str = Header(...)):
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
        home_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        folder_name = home_dir + f'/fait_front_res/{name}'
        result = {}
        for folder in os.listdir(folder_name):
            folder_path = os.path.join(folder_name, folder)
            if os.path.isdir(folder_path):
                files = os.listdir(folder_path)
                result[folder] = files

        return Response(
            status_code=status.HTTP_200_OK,
            message=f"Request Successful.",
            data=result,
            detail=None
        )
    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch image folder '{name}': {str(e)}",
            data=None,
            detail=None
        )


@router.get("/backend_res/html/{html_file}", summary="Fetch generated HTML file", tags=["backend_options"])
async def get_html_file(html_file: str = Path(...,example="001a-001a-001a-001a-00001a", description="file name"), token: str = Header(...)):
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
        home_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        folder_name = home_dir + f'/fait_back_res/{html_file}.html'
        result = {}

        return Response(
            status_code=status.HTTP_200_OK,
            message=f"Request Successful.",
            data=result,
            detail=None
        )
    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch image folder '{html_file}': {str(e)}",
            data=None,
            detail=None
        )
