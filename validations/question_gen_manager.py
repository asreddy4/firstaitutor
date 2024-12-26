import os
from pydantic import BaseModel, Field, EmailStr, constr, validator, conlist, conint,field_validator,model_validator
from typing import Optional, Dict, Union, List, Any, Literal
from datetime import date

class QuestionTypeRegister(BaseModel):
    """
    Data model for the Question Gen Manager table.

    Attributes:
    - qt_id (str): The unique identifier for the question_type based on node types.
      - Example: "001a-001a-001a-001a-0001a"
      - Description: Format of 'qt_id' depends on 'ln_id'.
    - q_variation (str): The question information of question.
      - Example: "englishuk"
      - Description: The title must be a non-empty string.
    - qt_format (str): The question format of question type.
      - Example: match
      - Description: Question format of question type. Must be one of "match", "blank", or "selection".
    - q_assigned_to (str) : Name of person who is going to create.
      - Example: "John Wick"
      - Description: A person who is creating question.
    - q_spec (Optional[str]): The q_spec must be in html format.
      - Example: <h1>Welcome</h1>
      - Description: The question spec should be html code.
    """


    qt_id: str = Field(
        ...,
        description="The unique identifier for the question_type based on node types.",
        example="001a-001a-001a-001a-0001a"
    )
    q_variation: str = Field(
        ...,
        description="The title of the question variation",
        example="englishuk"
    )
    q_assigned_to: str = Field(
        ...,
        description="A person with having approval access.",
        example="John Wick"
    )
    q_spec: Optional[str] = Field(
        ...,
        description="The question spec should be html code",
        example="<h1>Welcome</h1>"
    )

    @validator('qt_id')
    def validate_qt_id(cls, value):
        try:
            cls.qt_id = value
            parts = value.split('-')
        except Exception as e:
            raise ValueError(e)
        for i in range(len(parts) - 1):
            if i != len(parts) - 1:
                if len(parts[i]) != 4:
                    raise ValueError("first 4 ids must be exactly 4 characters long.")
                if not parts[i][:3].isdigit():
                    raise ValueError("The first three characters of id must be digits.")
                if not parts[i][3].islower():
                    raise ValueError("The last character of id must be a lowercase letter.")
        if len(parts[-1]) != 5:
            raise ValueError("last id must be exactly 5 characters long.")
        if not parts[-1][:4].isdigit():
            raise ValueError("The first four characters of id must be digits.")
        if not parts[-1][4].islower():
            raise ValueError("The last character of id must be a lowercase letter.")
        return value


class QuestionCreatorApproval(BaseModel):
    """
    Response model for Question Creator.

    Attributes:
    - qt_id (str): The unique identifier for the question_type based on node types.
      - Example: "001a-001a-001a-001a-0001a"
      - Description: Format of 'qt_id' depends on 'ln_id'.
    - q_variation (str): The question information of question.
      - Example: "englishuk"
      - Description: The title must be a non-empty string.
    - q_creator_approved (bool) : Indicates if the question is approved.
      - Example: "True"
      - Description: A boolean indicating whether the question approved by question creator.
    """
    qt_id: str = Field(
        ...,
        description="The unique identifier for the question_type based on node types.",
        example="001a-001a-001a-001a-0001a"
    )
    q_variation: str = Field(
        ...,
        description="The title of the question variation",
        example="englishuk"
    )
    q_creator_approved: bool = Field(
        ...,
        description="A boolean indicating whether the question approved by question creator.",
        example=False
    )


class QuestionManagerApproval(BaseModel):
    """
    Response model for Question Manager Approval.

    Attributes:
    - qt_id (str): The unique identifier for the question_type based on node types.
      - Example: "001a-001a-001a-001a-0001a"
      - Description: Format of 'qt_id' depends on 'ln_id'.
    - q_variation (str): The question information of question.
      - Example: "englishuk"
      - Description: The title must be a non-empty string.
    - q_json_file_exist (bool): A boolean indicating whether the json file exists.
      - Example: "False"
      - Description: A boolean indicating whether the json file exists.
    - q_html_file_exist (bool): A boolean indicating whether the html file exists.
      - Example: "False"
      - Description: A boolean indicating whether the html file exists.
    - q_html_file_link (str): The HTML link of the question.
      - Example: "001a-001a-001a-001a-0001a.html"
      - Description: The HTML link of the question.
    - q_manager_approved (bool) : Indicates if the question is approved.
      - Example: "False"
      - Description: A boolean indicating whether the question approved by manager.
    """
    qt_id: str = Field(
        ...,
        description="The unique identifier for the question_type based on node types.",
        example="001a-001a-001a-001a-0001a"
    )
    q_variation: str = Field(
        ...,
        description="The title of the question variation",
        example="englishuk"
    )
    q_json_file_exist: bool = Field(
        ...,
        description="A boolean indicating whether the json file exists.",
        example=False
    )
    q_html_file_exist: bool = Field(
        ...,
        description="A boolean indicating whether the html file exists.",
        example=False
    )
    q_html_file_link: str = Field(
        ...,
        description="The HTML link of the question",
        example="001a-001a-001a-001a-0001a.html"
    )
    q_manager_approved: bool = Field(
        ...,
        description="A boolean indicating whether the question approved by manager.",
        example=False
    )


class QuestionGen(BaseModel):
    q_num_db: int = Field(
        ...,
        description="The number of current questions for this variation in the db.",
        example=0
    )
    q_unused_db: int = Field(
        ...,
        example=0,
        description="The number of questions in the db that has not been used by any user."
    )

    @validator('q_num_db')
    def validate_q_num_db(cls, value):
        if not isinstance(value, int):
            raise ValueError("q_num_db must be integer")
        return value

    @validator('q_unused_db')
    def validate_q_unused_db(cls, value):
        if not isinstance(value, int):
            raise ValueError("q_unused_db must be integer")
        return value


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


