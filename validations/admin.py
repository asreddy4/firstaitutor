from pydantic import BaseModel, EmailStr, Field, constr
from typing import Literal, Optional, Union, Dict, List

class Login(BaseModel):
    """
    Request model for super admin login.

    Attributes:
    - email (str): The email address of the super admin.
      - Example: "user@example.com"
      - Description: The email address of the super admin.
    - password (str): The password for login.
      - Example: "secure_password"
      - Description: The password for login.
    """
    email: str = Field(
        ...,
        min_length=5,
        max_length=60,
        description="The email address of the super admin.",
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

class SuperAdminRegistration(BaseModel):
    """
    Request model for user registration.

    Attributes:
    - email (str): The email address of the user. Must be a valid email format.
      - Example: "user@example.com"
      - Description: The email address of the user.
    - fullname (str): The fullname of the user.
      - Example: "John Wick"
    - user_type (str): The type of the user. Must be one of 'admin' or 'business_manager' or 'content_manager', or 'question_creator'.
      - Example: "admin"
      - Description: The type of the user.
    """
    email: EmailStr = Field(
        ...,
        description="The email address of the user. Must be a valid email format.",
        example="user@example.com"
    )
    fullname: str = Field(
        ...,
        description="Fullname of the user.",
        example="John Wick"
    )
    user_type: Literal["admin", "business_manager", "content_manager", "question_creator"] = Field(
        ...,
        description="The type of the user. Must be one of 'admin' or 'business_manager' or 'content_manager', or 'question_creator'.",
        example="admin"
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

class AdminRegistration(BaseModel):
    """
    Request model for user registration.

    Attributes:
    - email (str): The email address of the user. Must be a valid email format.
      - Example: "user@example.com"
      - Description: The email address of the user.
    - fullname (str): The fullname of the user.
      - Example: "John Wick"
    - user_type (str): The type of the user. Must be one of 'business_manager' or 'content_manager', or 'question_creator'.
      - Example: "question_creator"
      - Description: The type of the user.
    """
    email: EmailStr = Field(
        ...,
        description="The email address of the user. Must be a valid email format.",
        example="user@example.com"
    )
    fullname: str = Field(
        ...,
        description="Fullname of the user.",
        example="John Wick"
    )
    user_type: Literal["business_manager", "content_manager", "question_creator"] = Field(
        ...,
        description="The type of the user. Must be one of 'super_admin' or 'business_manager' or 'content_manager', or 'question_creator'.",
        example="question_creator"
    )
    class Config:
        orm_mode = True

class CompleteRegistration(BaseModel):
    """
    Request model for complete registration.
    - email (str): The email address of the user. Must be a valid email format.
      - Example: "user@example.com"
      - Description: The email address of the user.
    - whatsapp_number (str): The whatsapp number of user. Must be at least 10 digits long.
      - Example: "+1234567890"
      - Description: The whatsapp number of the user.
    - telegram_number (str): The telegram number of user. Must be at least 10 digits long.
      - Example: "+1234567890"
      - Description: The telegram number of the user.
    - country (str): The country name of the user.
      - Example: "India"
      - Description: The country name of the user.
    - password (str): The password for registration. Must be at least 8 characters long.
      - Example: "secure_password"
      - Description: The password for registration.
    """
    email: EmailStr = Field(
        ...,
        description="The email address of the user. Must be a valid email format.",
        example="user@example.com"
    )

    whatsapp_number: Optional[constr(min_length=10, max_length=15)] = Field(
        ...,
        description="The whatsapp number of the user.",
        example="+1234567890"
    )
    telegram_number: Optional[constr(min_length=10, max_length=15)] = Field(
        ...,
        description="The telegram number of the user.",
        example="+1234567890"
    )
    country: str = Field(
        ...,
        description="The country name of the user.",
        example="India"
    )
    password: constr(min_length=8) = Field(
        ...,
        description="The password for registration. Must be at least 8 characters long.",
        example="secure_password"
    )

class DeleteAdmin(BaseModel):
    """
    Request model for deleting a learning_network.

    Attributes:
    - id (int): The unique identifier of the admin to delete.
      - Example: 1
      - Description: The ID of the admin that needs to be deleted.
    """

    id: int = Field(
        ...,
        description="The unique identifier of the admin that needs to be deleted.",
        example=1
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
    data: Optional[Union[Dict[str, Union[str, int, float, None]], List[Dict[str, Union[str, int, float, list, None]]]]] = Field(
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

