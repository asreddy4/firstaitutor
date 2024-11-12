from email.policy import default

from pydantic import BaseModel, Field, EmailStr, constr, validator, conlist, conint,field_validator,model_validator
from typing import Optional, Dict, Union, List,Any
from datetime import date
from typing import Literal
import re
from datetime import datetime
from pydantic_core.core_schema import FieldValidationInfo
from pypika import NullValue


class QuestionType(BaseModel):
    """
    Data model for the Question Type table.

    Attributes:
    - qt_id (str): The unique identifier for the question_type based on node types.
      - Example: "001a-001a-001a-001a-0001a"
      - Description: Format of 'qt_id' depends on 'ln_id'.
    - title (str): The title of the question type.
      - Example: "Match numbers between one and nine with their words"
      - Description: The title must be a non-empty string.
    - ln_id (str): The unique identifier for the learning network based on node types.
      - Example: "001a-001a-001a-001a"
      - Description: Format of 'ln_id' depends on 'is_keynode' and 'is_subject_head_node'.
    - q_id (str): The unique identifier for qualification.
      - Example: "0001"
      - Description: The qualification id must be non-empty string.
    - q_dict List(dict): A comma-separated list of dictionaries
      - Example: [
        {
            "qualification_id":  "000001",
            "qualification_title": "GCSE",
            "qualification_variations": ["Foundation","Higher"],
            "qualification_organisation": ["Edexcel", "AQA", "OCR", "CCEA", "WJEC"],
            "qualification_module": "Pure Mathematics 1",
            "qualification_study_level": "Key Stage 1",
            "qualification_grade": "U"
        },
        {
            "qualification_id":  "000002",
            "qualification_title": "GCSE",
            "qualification_variations": ["Foundation","Higher"],
            "qualification_organisation": ["Edexcel", "AQA", "OCR"],
            "qualification_module": "Pure Mathematics 2",
            "qualification_study_level": "Key Stage 2",
            "qualification_grade": "A"
        }
      ]
      - Description: The qualification dict with list of dictionaries one or more and qualification id should not be same
    - qt_age conint(ge=1, le=100): The maximum order of the question type.
      - Example: 25
      - Description: The age must be an integer between 1 and 100 inclusive..
    - qt_format (Optional[int]): The question format of question type.
      - Example: 2
      - Description: Optional integer value.
    - qt_order (Optional[int]): The question type order value must less than max_order of learning network.
      - Example: 1
      - Description: Optional integer value.
    - repeatable_pattern (str): The repeatable pattern of question type.
      - Example: "3-1-1"
      - Description: The question type repeatable pattern in times .
    - period_pattern (str): The period for repeating question type.
      - Example: "60-90"
      - Description: The required days to repeat the question type.
    - country_code (str): A two-letter uppercase country code.
      - Example: "GB"
      - Description: The country code must be a two-letter uppercase string.
    - page_script (text): JavaScript code used for UI changes
      - Example: "<script type="text/javascript"
                src="https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML">
                </script>"
      - Description: The javascript code must be in scripts tag
    - is_non_calculator (bool): Indicates question not required calculator
      - Example: True
      - Description: It indicates whether it question required calculator or not
    - min_time (int): Required minimum time for question
      - Example: 30
      - Description: The time must be an integer in seconds
    - max_time (int): Required maximum time for question
      - Example: 30
      - Description: The time must be an integer in seconds
    - end_time (int): Required total time for question
      - Example: 30
      - Description: The time must be an integer in seconds
    - learning_content (str): The learning content in html format
      - Example: "<h1>Welcome</h1>"
      - Description: The learning content should be html format
    """
    # - parent_nodes (Optional[str]): A comma-separated list of parent nodes.
    #   - Example: "001a-001a"
    #   - Description: Optional field that can be empty or a comma-separated list.

    qt_id: str = Field(
        ...,
        description="The unique identifier for the question_type based on node types.",
        example="001a-001a-001a-001a-0001a"
    )
    title: str = Field(
        ...,
        description="The title must be a non-empty string.",
        example="Match numbers between one and nine with their words"
    )
    ln_id: str = Field(
        ...,
        example="001a-001a-001a-001a",
        description="The unique identifier for the learning network based on node types."
    )
    # q_id: str = Field(
    #     ...,
    #     example="0001",
    #     description="The qualification id must be non-empty string."
    # )
    q_dict: List[dict] = Field(
        ...,
        example=[
            {
                "qualification_id": "000001",
                "qualification_title": "GCSE",
                "qualification_variations": ["Foundation", "Higher"],
                "qualification_organisation": ["Edexcel", "AQA", "OCR", "CCEA", "WJEC"],
                "qualification_module": "Pure Mathematics 1",
                "qualification_study_level": "Key Stage 1",
                "qualification_grade": "U"
            },
            {
                "qualification_id": "000002",
                "qualification_title": "GCSE",
                "qualification_variations": ["Foundation", "Higher"],
                "qualification_organisation": ["Edexcel", "AQA", "OCR"],
                "qualification_module": "Pure Mathematics 2",
                "qualification_study_level": "Key Stage 2",
                "qualification_grade": "A"
            }
        ],
        description="The qualification dict with list of dictionaries one or more and qualification id should not be same."
    )
    qt_age: conint(ge=1, le=100) = Field(
        ...,
        example=25,
        description="The age must be an integer between 1 and 100 inclusive.",
    )
    qt_format: Optional[int] = Field(
        ...,
        example=None,
        description="Optional integer value."
    )
    qt_order: Optional[int] = Field(
        ...,
        example=1,
        description="Optional integer value."
    )
    repeatable_pattern: str = Field(
        default=None,
        description="The question type repeatable pattern in times.",
        example="3-1-1"
    )
    period_pattern: str = Field(
        default=None,
        description="The required days to repeat the question type.",
        example="60-90"
    )
    country_id: str = Field(
        default=None,
        description="The country code must be a two-letter uppercase string.",
        example="GB"
    )
    page_script: str = Field(
        default=None,
        description="The javascript code must be in scripts tag.",
        example= '<script type="text/javascript" src="https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML"></script>'

    )
    is_non_calculator: bool = Field(
        default=True,
        description="It indicates calculator not required for this question",
        example=True
    )
    min_time: conint(ge=1) = Field(
        ...,
        description="The time must be an integer in seconds",
        example=30
    )
    max_time: conint(ge=1) = Field(
        ...,
        description="The time must be an integer in seconds",
        example=30
    )
    end_time: conint(ge=1) = Field(
        ...,
        description="The time must be an integer in seconds",
        example=30
    )
    learning_content: str = Field(
        ...,
        description="The learning content should be html format",
        example="<h1>Welcome</h1>"
    )

    @validator('qt_id')
    def validate_qt_id(cls, value):
        try:
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

    @validator('ln_id')
    def validate_ln_id(cls, value):
        try:
            ln_id_lst = value.split('-')
        except Exception as e:
            raise ValueError(e)
        for i in ln_id_lst:
            if len(i) != 4:
                raise ValueError("id must be exactly 4 characters long.")
            if not i[:3].isdigit():
                raise ValueError("The first three characters of id must be digits.")
            if not i[3].islower():
                raise ValueError("The last character of id must be a lowercase letter.")
        return value

    @validator('q_dict')
    def validate_q_dict(cls, value):
        if type(value) != list:
            raise ValueError("qualification dictionary must be a list with one or more dictionaries")
        q_dict_ids = [item['qualification_id'] for item in value]
        if len(q_dict_ids) != len(set(q_dict_ids)):
            raise ValueError("qualification ids should not be same")
        qualification_title = ["GCSE"]
        qualification_variations = ["Foundation", "Higher"]
        qualification_organisation = ["Edexcel", "AQA", "OCR", "CCEA", "WJEC"]
        qualification_study_level = ['Key Stage 1', 'Key Stage 2', 'Key Stage 3', 'Key Stage 4 (GCSE)', 'N1', 'N2', 'N3', 'N4', 'N5', 'AS', 'ALevel']
        qualification_grade = [1, 2, 3, 4, 5, 6, 7, 8, 9, "U", "A"]
        for item in value:
            if item['qualification_title'] is None:
                raise ValueError("qualification_title should not empty")
            if item['qualification_title'] not in qualification_title:
                raise ValueError(f"Value '{item['qualification_title']}' is not valid for 'qualification_title' list{qualification_title}.")
            if item['qualification_variations'] is not None:
                for item_lst in item['qualification_variations']:
                    if item_lst not in qualification_variations:
                        raise ValueError(f"Value '{item_lst}' is not valid for 'qualification_variations' list{qualification_variations}.")
            if item['qualification_organisation'] is not None:
                for item_lst in item['qualification_organisation']:
                    if item_lst not in qualification_organisation:
                        raise ValueError(f"Value '{item_lst}' is not valid for 'qualification_organisation' list{qualification_organisation}.")
            if item['qualification_study_level'] is not None:
                if item['qualification_study_level'] not in qualification_study_level:
                    raise ValueError(f"Value '{item['qualification_study_level']}' is not valid for 'qualification_study_level' list{qualification_study_level}.")
            if item['qualification_grade'] is not None:
                if item['qualification_grade'] not in qualification_grade:
                    raise ValueError(f"Value '{item['qualification_grade']}' is not valid for 'qualification_grade' list{qualification_grade}.")
        return value

    @validator('repeatable_pattern')
    def validate_repeatable_pattern(cls, value):
        try:
            parts = value.split('-')
            cls.repeatable_length = len(parts)
            for i in parts:
                if not i.isdigit():
                    raise ValueError("The repeatable pattern should be integers with separation of '-' eg: '3-1-1' ")
        except Exception as e:
            raise ValueError(e)
        return value

    @validator('period_pattern')
    def validate_period_pattern(cls, value):
        try:
            parts = value.split('-')
            for i in parts:
                if not i.isdigit():
                    raise ValueError("The period pattern should be integers with separation of '-' eg: '60-90' ")
            if len(parts) != cls.repeatable_length -1:
                raise ValueError("The period pattern length should less than repeatable pattern eg: '60-90'(repeatable pattern: '3-1-1') ")
        except Exception as e:
            raise ValueError(e)
        return value

    @validator('country_id')
    def validate_country_code(cls, value):
        if len(value) != 2 or not value.isupper():
            raise ValueError('Country id must be exactly 2 uppercase letters.')
        return value


    # @validator('q_id')
    # def validate_q_id(cls, value):
    #     if len(value) != 6 or not value.isdigit():
    #         raise ValueError('The qualification ID must be a 6-digit number, zero-padded if necessary.')
    #     return value

class UpdateQuestionType(BaseModel):
    """
    Data model for the Question Type table.

    Attributes:
    - id (int): The unique identifier of the question type to be updated.
      - Example: 1
      - Description: The ID must be a positive integer representing the unique identifier of the question type to be updated.
    - qt_id (str): The unique identifier for the question_type based on node types.
      - Example: "001a-001a-001a-001a-0001a"
      - Description: Format of 'qt_id' depends on 'ln_id'.
    - title (str): The title of the question type.
      - Example: "Match numbers between one and nine with their words"
      - Description: The title must be a non-empty string.
    - ln_id (str): The unique identifier for the learning network based on node types.
      - Example: "001a-001a-001a-001a"
      - Description: Format of 'ln_id' depends on 'is_keynode' and 'is_subject_head_node'.
    - q_id (str): The unique identifier for qualification.
      - Example: "0001"
      - Description: The qualification id must be non-empty string.
    - q_dict List(dict): A comma-separated list of dictionaries
      - Example: [
        {
            "qualification_id":  "000001",
            "qualification_title": "GCSE",
            "qualification_variations": ["Foundation","Higher"],
            "qualification_organisation": ["Edexcel", "AQA", "OCR", "CCEA", "WJEC"],
            "qualification_module": "Pure Mathematics 1",
            "qualification_study_level": "Key Stage 1",
            "qualification_grade": "U"
        },
        {
            "qualification_id":  "000002",
            "qualification_title": "GCSE",
            "qualification_variations": ["Foundation","Higher"],
            "qualification_organisation": ["Edexcel", "AQA", "OCR"],
            "qualification_module": "Pure Mathematics 2",
            "qualification_study_level": "Key Stage 2",
            "qualification_grade": "A"
        }
      ]
      - Description: The qualification dict with list of dictionaries one or more and qualification id should not be same.
    - qt_age conint(ge=1, le=100): The maximum order of the question type.
      - Example: 25
      - Description: The age must be an integer between 1 and 100 inclusive.
    - qt_format (Optional[int]): The question format of question type.
      - Example: 2
      - Description: Optional integer value.
    - qt_order (Optional[int]): The question type order value must less than max_order of learning network.
      - Example: 1
      - Description: Optional integer value.
    - repeatable_pattern (str): The repeatable pattern of question type.
      - Example: "3-1-1"
      - Description: The question type repeatable pattern in times .
    - period_pattern (str): The period for repeating question type.
      - Example: "60-90"
      - Description: The required days to repeat the question type.
    - country_code (str): A two-letter uppercase country code.
      - Example: "GB"
      - Description: The country code must be a two-letter uppercase string.
    - page_script (text): JavaScript code used for UI changes
      - Example: "<script type="text/javascript"
                src="https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML">
                </script>"
      - Description: The javascript code must be in scripts tag
    - is_non_calculator (bool): Indicates question not required calculator
      - Example: True
      - Description: It indicates whether it question required calculator or not
    - min_time (int): Required minimum time for question
      - Example: 30
      - Description: The time must be an integer in seconds
    - max_time (int): Required maximum time for question
      - Example: 30
      - Description: The time must be an integer in seconds
    - end_time (int): Required total time for question
      - Example: 30
      - Description: The time must be an integer in seconds
    - learning_content (str): The learning content in html format
      - Example: "<h1>Welcome</h1>"
      - Description: The learning content should be html format
    """
    # - parent_nodes (Optional[str]): A comma-separated list of parent nodes.
    #   - Example: "001a-001a"
    #   - Description: Optional field that can be empty or a comma-separated list.
    id: int = Field(
        ...,
        description="The ID must be a positive integer representing the unique identifier of the question type to be updated.",
        example=1
    )
    qt_id: str = Field(
        ...,
        description="The unique identifier for the question_type based on node types.",
        example="001a-001a-001a-001a-0001a"
    )
    title: str = Field(
        ...,
        description="The title must be a non-empty string.",
        example="Match numbers between one and nine with their words"
    )
    ln_id: str = Field(
        ...,
        example="001a-001a-001a-001a",
        description="The unique identifier for the learning network based on node types."
    )
    # q_id: str = Field(
    #     ...,
    #     example="0001",
    #     description="The qualification id must be non-empty string."
    # )
    q_dict: List[dict] = Field(
        ...,
        example= [
            {
                "qualification_id": "000001",
                "qualification_title": "GCSE",
                "qualification_variations": ["Foundation", "Higher"],
                "qualification_organisation": ["Edexcel", "AQA", "OCR", "CCEA", "WJEC"],
                "qualification_module": "Pure Mathematics 1",
                "qualification_study_level": "Key Stage 1",
                "qualification_grade": "U"
            },
            {
                "qualification_id": "000002",
                "qualification_title": "GCSE",
                "qualification_variations": ["Foundation", "Higher"],
                "qualification_organisation": ["Edexcel", "AQA", "OCR"],
                "qualification_module": "Pure Mathematics 2",
                "qualification_study_level": "Key Stage 2",
                "qualification_grade": "A"
            }
        ],
        description="The qualification dict with list of dictionaries one or more and qualification id should not be same."
    )
    qt_age: conint(ge=1, le=100) = Field(
        ...,
        example=25,
        description="The age must be an integer between 1 and 100 inclusive.",
    )
    qt_format: Optional[int] = Field(
        ...,
        example=None,
        description="Optional integer value."
    )
    qt_order: Optional[int] = Field(
        ...,
        example=1,
        description="Optional integer value."
    )
    repeatable_pattern: str = Field(
        default=None,
        description="The question type repeatable pattern in times.",
        example="3-1-1"
    )
    period_pattern: str = Field(
        default=None,
        description="The required days to repeat the question type.",
        example="60-90"
    )
    country_id: str = Field(
        default=None,
        description="The country code must be a two-letter uppercase string.",
        example="GB"
    )
    page_script: str = Field(
        default=None,
        description="The javascript code must be in scripts tag.",
        example= '<script type="text/javascript" src="https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML"></script>'
    )
    is_non_calculator: bool = Field(
        default=True,
        description="It indicates question required calculator or not",
        example=True
    )
    min_time: conint(ge=1) = Field(
        ...,
        description="The time must be an integer in seconds",
        example=30
    )
    max_time: conint(ge=1) = Field(
        ...,
        description="The time must be an integer in seconds",
        example=30
    )
    end_time: conint(ge=1) = Field(
        ...,
        description="The time must be an integer in seconds",
        example=30
    )
    learning_content: str = Field(
        ...,
        description="The learning content should be html format",
        example="<h1>Welcome</h1>"
    )

    @validator('qt_id', always=True)
    def validate_qt_id(cls, value):
        try:
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

    @validator('ln_id', always=True)
    def validate_ln_id(cls, value):
        try:
            ln_id_lst = value.split('-')
        except Exception as e:
            raise ValueError(e)
        for i in ln_id_lst:
            if len(i) != 4:
                raise ValueError("id must be exactly 4 characters long.")
            if not i[:3].isdigit():
                raise ValueError("The first three characters of id must be digits.")
            if not i[3].islower():
                raise ValueError("The last character of id must be a lowercase letter.")
        return value

    @validator('q_dict', always=True)
    def validate_q_dict(cls, value):
        if type(value) != list:
            raise ValueError("qualification dictionary must be a list with one or more dictionaries")
        q_dict_ids = [item['qualification_id'] for item in value]
        if len(q_dict_ids) != len(set(q_dict_ids)):
            raise ValueError("qualification ids should not be same")
        qualification_title = ["GCSE"]
        qualification_variations = ["Foundation", "Higher"]
        qualification_organisation = ["Edexcel", "AQA", "OCR", "CCEA", "WJEC"]
        qualification_study_level = ['Key Stage 1', 'Key Stage 2', 'Key Stage 3', 'Key Stage 4 (GCSE)', 'N1', 'N2', 'N3', 'N4', 'N5', 'AS', 'ALevel']
        qualification_grade = [1, 2, 3, 4, 5, 6, 7, 8, 9, "U", "A"]
        for item in value:
            if item['qualification_title'] is None:
                raise ValueError("qualification_title should not empty")
            if item['qualification_title'] not in qualification_title:
                raise ValueError(f"Value '{item['qualification_title']}' is not valid for 'qualification_title' list{qualification_title}.")
            if item['qualification_variations'] is not None:
                for item_lst in item['qualification_variations']:
                    if item_lst not in qualification_variations:
                        raise ValueError(f"Value '{item_lst}' is not valid for 'qualification_variations' list{qualification_variations}.")
            if item['qualification_organisation'] is not None:
                for item_lst in item['qualification_organisation']:
                    if item_lst not in qualification_organisation:
                        raise ValueError(f"Value '{item_lst}' is not valid for 'qualification_organisation' list{qualification_organisation}.")
            if item['qualification_study_level'] is not None:
                if item['qualification_study_level'] not in qualification_study_level:
                    raise ValueError(f"Value '{item['qualification_study_level']}' is not valid for 'qualification_study_level' list{qualification_study_level}.")
            if item['qualification_grade'] is not None:
                if item['qualification_grade'] not in qualification_grade:
                    raise ValueError(f"Value '{item['qualification_grade']}' is not valid for 'qualification_grade' list{qualification_grade}.")
        return value

    @validator('repeatable_pattern', always=True)
    def validate_repeatable_pattern(cls, value):
        try:
            parts = value.split('-')
            cls.repeatable_length = len(parts)
            for i in parts:
                if not i.isdigit():
                    raise ValueError("The repeatable pattern should be integers with separation of '-' eg: '3-1-1' ")
        except Exception as e:
            raise ValueError(e)
        return value

    @validator('period_pattern', always=True)
    def validate_period_pattern(cls, value):
        try:
            parts = value.split('-')
            for i in parts:
                if not i.isdigit():
                    raise ValueError("The period pattern should be integers with separation of '-' eg: '60-90' ")
            if len(parts) != cls.repeatable_length -1:
                raise ValueError("The period pattern length should less than repeatable pattern eg: '60-90'(repeatable pattern: '3-1-1') ")
        except Exception as e:
            raise ValueError(e)
        return value

    @validator('country_id', always=True)
    def validate_country_code(cls, value):
        if len(value) != 2 or not value.isupper():
            raise ValueError('Country id must be exactly 2 uppercase letters.')
        return value


class DeleteQuestionType(BaseModel):
    """
    Request model for deleting a question type.

    Attributes:
    - id (int): The unique identifier of the question type to delete.
      - Example: 1
      - Description: The ID of the question type that needs to be deleted.
    """

    id: int = Field(
        ...,
        description="The unique identifier of the question type that needs to be deleted.",
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


