from pydantic import BaseModel, Field, EmailStr, constr, validator, conlist, conint,field_validator,model_validator
from typing import Optional, Dict, Union, List,Any
from datetime import date
from typing import Literal
import re
import os
import sys
from datetime import datetime
from pydantic_core.core_schema import FieldValidationInfo

class Register(BaseModel):
    """
    Request model for user registration.

    Attributes:
    - email (str): The email address of the user. Must be a valid email format.
      - Example: "user@example.com"
      - Description: The email address of the user.
    - phone (str): The phone number of the user. Must be at least 10 digits long.
      - Example: "+1234567890"
      - Description: The phone number of the user.
    - date_of_birth (date): The date of birth of the user. Must be a valid date.
      - Example: "1990-01-01"
      - Description: The date of birth of the user.
    - country_name (str): The name of the user's country. Must be between 2 and 50 characters.
      - Example: "Iran"
      - Description: The name of the user's country.
    - city_name (str): The name of the user's city. Must be between 2 and 50 characters.
      - Example: "Tehran"
      - Description: The name of the user's city.
    - school_name (str): The name of the user's school. Must be between 2 and 100 characters.
      - Example: "Example High School"
      - Description: The name of the user's school.
    - user_type (str): The type of the user. Must be one of "admin", "student", or "ordinary".
      - Example: "student"
      - Description: The type of the user.
    - password (str): The password for registration. Must be at least 8 characters long.
      - Example: "secure_password"
      - Description: The password for registration.
    """
    email: EmailStr = Field(
        ...,
        description="The email address of the user. Must be a valid email format.",
        example="user@example.com"
    )
    phone: constr(min_length=10, max_length=15) = Field(
        ...,
        description="The phone number of the user. Must be at least 10 digits long.",
        example="+1234567890"
    )
    date_of_birth: date = Field(
        ...,
        description="The date of birth of the user. Must be a valid date.",
        example="1990-01-01"
    )
    country_name: str = Field(
        ...,
        description="The name of the user's country. Must be between 2 and 50 characters.",
        example="United Kingdom"
    )
    city_name: str = Field(
        ...,
        description="The name of the user's city. Must be between 2 and 50 characters.",
        example="Westminster"
    )
    school_name: constr(min_length=2, max_length=100) = Field(
        ...,
        description="The name of the user's school. Must be between 2 and 100 characters.",
        example="Example High School"
    )
    user_type: Literal["admin", "student", "ordinary"] = Field(
        ...,
        description="The type of the user. Must be one of 'admin', 'student', or 'ordinary'.",
        example="student"
    )
    password: constr(min_length=8) = Field(
        ...,
        description="The password for registration. Must be at least 8 characters long.",
        example="secure_password"
    )

    class Config:
        orm_mode = True


class Login(BaseModel):
    """
    Request model for user login.

    Attributes:
    - email (str): The email address of the user.
      - Example: "user@example.com"
      - Description: The email address of the user.
    - password (str): The password for login.
      - Example: "secure_password"
      - Description: The password for login.
    """
    email: str = Field(
        ...,
        min_length=5,
        max_length=60,
        description="The email address of the user.",
        example="user@example.com"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=20,
        description="The password for login.",
        example="secure_password"
    )

    class Config:
        orm_mode = True


class Logout(BaseModel):
    """
    Represents a request to Log out a user based on a token.

    Attributes:
        token (str): The token associated with the user to logout.
    """

    token: str = Field(
        ...,
        min_length=8,
        max_length=16,
        title="Token",
        description="The token associated with the user to logout.",
        example="e3593ee36f6f35ec"
    )

class Response(BaseModel):
    """
    Response model for API responses.

    Attributes:
    - status_code (int): The status code of the response.
    - message (str): A message describing the response.
    - data (Optional[Union[Dict[str, Union[str, int, float]], List[Dict[str, Union[str, int, float]]]]]): Optional data associated with the response.
    - detail (Optional[List[Dict[str, str]]]): Optional details about errors or additional information.
    """

    status_code: int = Field(...,
                             description="The status code of the response. Should be one of 200 (OK), 300 (Warning),"
                                         " or 400 (Error).",
                             example=200)
    message: str = Field(..., description="A message describing the response.", example="OK")
    data: Optional[Union[Dict[str, Union[str, int, float]], List[Dict[str, Union[str, int, float, list]]]]] = Field(
        None,
        description="Optional data associated with the response. Should be provided as either a dictionary or a list of dictionaries.",
        example=[{
            "name": "John Doe",
            "age": 30},
            {
                "name": "Jane Doe",
                "age": 28}])
    detail: Optional[List[Dict[str, str]]] = Field(None,
                                                   description="Optional details about errors or additional information.",
                                                   example=[
                                                       {"loc": ["body", "price"], "msg": "value is not a valid float",
                                                        "type": "type_error.float"}])


def name():
    pass