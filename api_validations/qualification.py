from pydantic import BaseModel, Field, EmailStr, constr, validator, conlist, conint,field_validator,model_validator
from typing import Optional, Dict, Union, List,Any
from datetime import date
from typing import Literal
import re
import os
import sys
from datetime import datetime
from pydantic_core.core_schema import FieldValidationInfo

class QualificationRequest(BaseModel):
    """
    Request model for creating a new qualification.

    Attributes:
    - title (str): The title of the qualification.
      - Example: "Mathematics"
      - Description: The title must be a non-empty string.
    - country_code (str): A two-letter uppercase country code.
      - Example: "GB"
      - Description: The country code must be a two-letter uppercase string.
    - subject_id (int): An integer identifier for the subject.
      - Example: 123
      - Description: The subject ID must be an integer and cannot be empty.
    - age (int): The age of the individual.
      - Example: 25
      - Description: The age must be an integer between 1 and 100 inclusive.
    - var (List[str]): A list containing one or both of the values 'Foundation' and 'Higher'.
      - Example: ["Foundation", "Higher"]
      - Description: The 'var' field must be a list containing one or both of the following values: 'Foundation' and 'Higher'.
    - org (List[str]): A list containing one or more of the approved organizations.
      - Example: ["Edexcel", "AQA"]
      - Description: The 'org' field must be a list containing one or more of the following values: ['Edexcel', 'AQA', 'OCR', 'CCEA', 'WJEC', 'SQL'].
    - steps (List[str]): A list containing one or more of the approved steps.
      - Example: ["Key Stage 1", "Key Stage 2"]
      - Description: The 'steps' field must be a list containing one or more of the following values: ['Key Stage 1', 'Key Stage 2', 'Key Stage 3', 'Key Stage 4 (GCSE)', 'N1', 'N2', 'N3', 'N4', 'N5', 'AS', 'ALevel'].
    - grade (List[str]): A list containing one or more of the approved grades.
      - Example: ["A", "B"]
      - Description: The 'grade' field must be a list containing one or more of the following values: ['U', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D'].
    - modules (Optional[List[str]]): An optional list of modules.
      - Example: ["Module 1", "Module 2"]
      - Description: An optional list of modules that can be empty or contain string values.
    """

    # q_id: str = Field(
    #     ...,
    #     description="The qualification ID must be a 6-digit number, zero-padded if necessary.",
    #     example="000001"
    # )

    title: str = Field(
        ...,
        description="The title must be a non-empty string.",
        example="Mathematics"
    )

    country_code: str = Field(
        ...,
        description="The country code must be a two-letter uppercase string.",
        example="GB"
    )

    subject_id: int = Field(
        ...,
        description="The subject ID must be an integer and cannot be empty.",
        example=123
    )

    age: conint(ge=1, le=100) = Field(
        ...,
        description="The age must be an integer between 1 and 100 inclusive.",
        example=25
    )

    var: List[str] = Field(
        None,
        description="The 'var' field must be a list containing one or both of the following values: 'Foundation' and 'Higher'.",
        example=['Foundation', 'Higher']
    )

    org: List[str] = Field(
        None,
        description="The 'org' field must be a list containing one or more of the following values: ['Edexcel', 'AQA', 'OCR', 'CCEA', 'WJEC', 'SQL'].",
        example=['Edexcel', 'AQA']
    )

    steps: List[str] = Field(
        None,
        description="The 'steps' field must be a list containing one or more of the following values: ['Key Stage 1', 'Key Stage 2', 'Key Stage 3', 'Key Stage 4 (GCSE)', 'N1', 'N2', 'N3', 'N4', 'N5', 'AS', 'ALevel'].",
        example=['Key Stage 1', 'Key Stage 2']
    )

    grade: List[str] = Field(
        None,
        description="The 'grade' field must be a list containing one or more of the following values: ['U', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D'].",
        example=['A', 'B']
    )

    modules: Optional[List[str]] = Field(
        default=[],
        description="An optional list of modules that can be empty or contain string values.",
        example=['Module 1', 'Module 2']
    )

    # @validator('q_id')
    # def validate_q_id(cls, value):
    #     if len(value) != 6 or not value.isdigit():
    #         raise ValueError('The qualification ID must be a 6-digit number, zero-padded if necessary.')
    #     return value

    @validator('country_code')
    def validate_country_code(cls, value):
        if len(value) != 2 or not value.isupper():
            raise ValueError('Country code must be exactly 2 uppercase letters.')
        return value

    @validator('var')
    def validate_var(cls, value):
        allowed_values = ['Foundation', 'Higher']
        if value is None:
            return value
        if len(value) < 1 or len(value) > 2:
            raise ValueError(
                'The "var" field must contain one or both of the following values: "Foundation" and "Higher".')
        for item in value:
            if item not in allowed_values:
                raise ValueError(f"Value '{item}' is not valid for 'var'.")
        return value

    @validator('org')
    def validate_org(cls, value):
        allowed_values = ['Edexcel', 'AQA', 'OCR', 'CCEA', 'WJEC', 'SQL']
        if value is None:
            return value
        if len(value) < 1:
            raise ValueError('The "org" field must contain at least one value.')
        for item in value:
            if item not in allowed_values:
                raise ValueError(f"Value '{item}' is not valid for 'org'.")
        return value

    @validator('steps')
    def validate_steps(cls, value):
        allowed_values = ['Key Stage 1', 'Key Stage 2', 'Key Stage 3', 'Key Stage 4 (GCSE)', 'N1', 'N2', 'N3', 'N4',
                          'N5', 'AS', 'ALevel']
        if value is None:
            return value
        if len(value) < 1:
            raise ValueError('The "steps" field must contain at least one value.')
        for item in value:
            if item not in allowed_values:
                raise ValueError(f"Value '{item}' is not valid for 'steps'.")
        return value

    @validator('grade')
    def validate_grade(cls, value):
        allowed_values = ['U', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D']
        if value is None:
            return value
        if len(value) < 1:
            raise ValueError('The "grade" field must contain at least one value.')
        for item in value:
            if item not in allowed_values:
                raise ValueError(f"Value '{item}' is not valid for 'grade'.")
        return value


class QualificationUpdateRequest(BaseModel):
    """
    Request model for updating an existing qualification.

    Attributes:
    - id (int): The unique identifier of the qualification to be updated.
      - Example: 1
      - Description: The ID must be a positive integer representing the unique identifier of the qualification to be updated.
    - title (Optional[str]): The title of the qualification.
      - Example: "Mathematics"
      - Description: The title must be a non-empty string if provided.
    - country_code (Optional[str]): A two-letter uppercase country code.
      - Example: "GB"
      - Description: The country code must be a two-letter uppercase string if provided.
    - subject_id (Optional[int]): An integer identifier for the subject.
      - Example: 123
      - Description: The subject ID must be an integer and cannot be empty if provided.
    - age (Optional[int]): The age of the individual.
      - Example: 25
      - Description: The age must be an integer between 1 and 100 inclusive if provided.
    - var (Optional[List[str]]): A list containing one or both of the values 'Foundation' and 'Higher'.
      - Example: ["Foundation", "Higher"]
      - Description: The 'var' field must be a list containing one or both of the following values: 'Foundation' and 'Higher' if provided.
    - org (Optional[List[str]]): A list containing one or more of the approved organizations.
      - Example: ["Edexcel", "AQA"]
      - Description: The 'org' field must be a list containing one or more of the following values: ['Edexcel', 'AQA', 'OCR', 'CCEA', 'WJEC', 'SQL'] if provided.
    - steps (Optional[List[str]]): A list containing one or more of the approved steps.
      - Example: ["Key Stage 1", "Key Stage 2"]
      - Description: The 'steps' field must be a list containing one or more of the following values: ['Key Stage 1', 'Key Stage 2', 'Key Stage 3', 'Key Stage 4 (GCSE)', 'N1', 'N2', 'N3', 'N4', 'N5', 'AS', 'ALevel'] if provided.
    - grade (Optional[List[str]]): A list containing one or more of the approved grades.
      - Example: ["A", "B"]
      - Description: The 'grade' field must be a list containing one or more of the following values: ['U', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D'] if provided.
    - modules (Optional[List[str]]): An optional list of modules.
      - Example: ["Module 1", "Module 2"]
      - Description: An optional list of modules that can be empty or contain string values.
    """

    id: int = Field(
        ...,
        description="The ID must be a positive integer representing the unique identifier of the qualification to be updated.",
        example=1
    )

    title: Optional[str] = Field(
        None,
        description="The title must be a non-empty string if provided.",
        example="Mathematics"
    )

    country_code: Optional[str] = Field(
        None,
        description="The country code must be a two-letter uppercase string if provided.",
        example="GB"
    )

    subject_id: Optional[int] = Field(
        None,
        description="The subject ID must be an integer and cannot be empty if provided.",
        example=123
    )

    age: Optional[conint(ge=1, le=100)] = Field(
        None,
        description="The age must be an integer between 1 and 100 inclusive if provided.",
        example=25
    )

    var: Optional[List[str]] = Field(
        None,
        description="The 'var' field must be a list containing one or both of the following values: 'Foundation' and 'Higher' if provided.",
        example=['Foundation', 'Higher']
    )

    org: Optional[List[str]] = Field(
        None,
        description="The 'org' field must be a list containing one or more of the following values: ['Edexcel', 'AQA', 'OCR', 'CCEA', 'WJEC', 'SQL'] if provided.",
        example=['Edexcel', 'AQA']
    )

    steps: Optional[List[str]] = Field(
        None,
        description="The 'steps' field must be a list containing one or more of the following values: ['Key Stage 1', 'Key Stage 2', 'Key Stage 3', 'Key Stage 4 (GCSE)', 'N1', 'N2', 'N3', 'N4', 'N5', 'AS', 'ALevel'] if provided.",
        example=['Key Stage 1', 'Key Stage 2']
    )

    grade: Optional[List[str]] = Field(
        None,
        description="The 'grade' field must be a list containing one or more of the following values: ['U', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D'] if provided.",
        example=['A', 'B']
    )

    modules: Optional[List[str]] = Field(
        default=[],
        description="An optional list of modules that can be empty or contain string values.",
        example=['Module 1', 'Module 2']
    )

    @validator('country_code', always=True)
    def validate_country_code(cls, value):
        if value is not None:
            if len(value) != 2 or not value.isupper():
                raise ValueError('Country code must be exactly 2 uppercase letters.')
        return value

    @validator('var', always=True)
    def validate_var(cls, value):
        if value is not None:
            allowed_values = ['Foundation', 'Higher']
            if value is None:
                return value
            if len(value) < 1 or len(value) > 2:
                raise ValueError(
                    'The "var" field must contain one or both of the following values: "Foundation" and "Higher".')
            for item in value:
                if item not in allowed_values:
                    raise ValueError(f"Value '{item}' is not valid for 'var'.")
        return value

    @validator('org', always=True)
    def validate_org(cls, value):
        if value is None:
            return value
        if value is not None:
            allowed_values = ['Edexcel', 'AQA', 'OCR', 'CCEA', 'WJEC', 'SQL']
            if len(value) < 1:
                raise ValueError('The "org" field must contain at least one value.')
            for item in value:
                if item not in allowed_values:
                    raise ValueError(f"Value '{item}' is not valid for 'org'.")
        return value

    @validator('steps', always=True)
    def validate_steps(cls, value):
        if value is None:
            return value
        if value is not None:
            allowed_values = ['Key Stage 1', 'Key Stage 2', 'Key Stage 3', 'Key Stage 4 (GCSE)', 'N1', 'N2', 'N3', 'N4',
                              'N5', 'AS', 'ALevel']
            if len(value) < 1:
                raise ValueError('The "steps" field must contain at least one value.')
            for item in value:
                if item not in allowed_values:
                    raise ValueError(f"Value '{item}' is not valid for 'steps'.")
        return value

    @validator('grade', always=True)
    def validate_grade(cls, value):
        if value is None:
            return value
        if value is not None:
            allowed_values = ['U', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D']
            if len(value) < 1:
                raise ValueError('The "grade" field must contain at least one value.')
            for item in value:
                if item not in allowed_values:
                    raise ValueError(f"Value '{item}' is not valid for 'grade'.")
        return value

class DeleteQualification(BaseModel):
    """
    Request model for deleting a qualification.

    Attributes:
    - id (int): The unique identifier of the qualification to delete.
      - Example: 1
      - Description: The ID of the qualification that needs to be deleted.
    """

    id: int = Field(
        ...,
        description="The unique identifier of the qualification that needs to be deleted.",
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

