import os.path

from pydantic import BaseModel, Field, EmailStr, constr, validator, conlist, conint,field_validator,model_validator
from typing import Optional, Dict, Union, List,Any
from datetime import date
from typing import Literal
import re
from datetime import datetime
from pydantic_core.core_schema import FieldValidationInfo
from pypika import NullValue
import json

country_json_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
country_json = country_json_dir +'/utils/country.json'

def read_country_json(file_path : str ):
    with open(file_path, 'r') as file:
        country_json_dict = json.load(file)
    country_list = [country["alpha2"] for country in country_json_dict]
    return country_list

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
    - parent_nodes (Optional[List[str]]): A comma-separated list of parent nodes.
      - Example: [001a-001a-001a-001a-0001a','001a-001a-001a-001a-0002a']
      - Description: Optional field that can be empty or a comma-separated list.
    - qual_dict List(dict): A comma-separated list of dictionaries
      - Example: [
        {
            "qualification_id":  "000001",
            "qualification_title": "GCSE",
            "qualification_variations": ["Foundation","Higher"],
            "qualification_organisation": ["Edexcel", "AQA", "OCR", "CCEA", "WJEC"],
            "typical_mark": {
                "Edexcel": 4,
                "AQA": "correct/incorrect",
                "OCR": 3,
                "CCEA": 4,
                "WJEC": 4
            }
            "qualification_module": ["Pure Mathematics 1"],
            "qualification_study_level": "Key Stage 1",
            "qualification_grade": "U"
        },
        {
            "qualification_id":  "000002",
            "qualification_title": "GCSE",
            "qualification_variations": ["Foundation","Higher"],
            "qualification_organisation": ["Edexcel", "AQA", "OCR"],
            "typical_mark": {
                "Edexcel": 4,
                "AQA": 4,
                "OCR": 3
            }
            "qualification_module": ["Pure Mathematics 2"],
            "qualification_study_level": "Key Stage 2",
            "qualification_grade": "A"
        }
      ]
      - Description: The qualification dict with list of dictionaries one or more and qualification id should not be same
    - qt_age conint(ge=1, le=100): The maximum order of the question type.
      - Example: 25
      - Description: The age must be an integer between 1 and 100 inclusive.
    - qt_format (str): The question format of question type.
      - Example: match
      - Description: Question format of question type. Must be one of "match", "blank", or "selection".
    - qt_order (Optional[int]): The question type order value must less than max_order of learning network.
      - Example: 1
      - Description: Optional integer value.
    - repeatable_pattern (str): The repeatable pattern of question type.
      - Example: "3|1|1"
      - Description: The question type repeatable pattern in times .
    - period_pattern (str): The period for repeating question type.
      - Example: "60|90"
      - Description: The required days to repeat the question type.
    - country_id (List[str]): A comma-separated list of two-letter uppercase country code.
      - Example: ["GB", "IN"]
      - Description: The list of country codes must be a two-letter uppercase string.
    - page_script (text): JavaScript code used for UI changes
      - Example: "<script type="text/javascript"
                src="https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML">
                </script>"
      - Description: The javascript code must be in scripts tag
    - is_non_calculator (bool): Indicates question not required calculator
      - Example: True
      - Description: It indicates whether it question required calculator or not
    - min_time (int): Required minimum time for question
      - Example: 10
      - Description: The time must be an integer in seconds and must be less than max_time
    - max_time (int): Required maximum time for question
      - Example: 20
      - Description: The time must be an integer in seconds and must be less than end_time
    - end_time (int): Required total time for question
      - Example: 30
      - Description: The time must be an integer in seconds
    - learning_content (str): The learning content in html format
      - Example: "<h1>Welcome</h1>"
      - Description: The learning content should be html format
    """


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
    parent_nodes: Optional[List[str]] = Field(
        ...,
        description="An optional comma-separated list of parent nodes.",
        example=['001a-001a-001a-001a-0001a','001a-001a-001a-001a-0002a']
    )
    qual_dict: List[dict] = Field(
        ...,
        example=[
            {
                "qualification_id": "000001",
                "qualification_title": "GCSE",
                "qualification_variations": ["Foundation", "Higher"],
                "qualification_organisation": ["Edexcel", "AQA", "OCR", "CCEA", "WJEC"],
                "typical_mark": {
                    "Edexcel": 4,
                    "AQA": "correct/incorrect",
                    "OCR": 3,
                    "CCEA": 4,
                    "WJEC": 4,
                },
                "qualification_module": ["Pure Mathematics 1"],
                "qualification_study_level": "Key Stage 1",
                "qualification_grade": "U"
            },
            {
                "qualification_id": "000002",
                "qualification_title": "GCSE",
                "qualification_variations": ["Foundation", "Higher"],
                "qualification_organisation": ["Edexcel", "AQA", "OCR"],
                "typical_mark": {
                    "Edexcel": 4,
                    "AQA": 4,
                    "OCR": 3
                },
                "qualification_module": ["Pure Mathematics 2"],
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
    qt_format: Literal["match", "blank", "selection"] = Field(
        ...,
        example='match',
        description="Question format of question type. Must be one of 'match', 'blank' or 'selection'."
    )
    qt_order: int = Field(
        ...,
        example=1,
        description="Optional integer value."
    )
    repeatable_pattern: str = Field(
        ...,
        description="The question type repeatable pattern in times.",
        example="3|1|1"
    )
    period_pattern: Optional[str] = Field(
        ...,
        description="The required days to repeat the question type.",
        example="60|90"
    )
    country_id: List[str] = Field(
        ...,
        description="The list of country codes must be a two-letter uppercase string",
        example=["GB", "IN"]
    )
    page_script: Optional[str] = Field(
        ...,
        description="The javascript code must be in scripts tag.",
        example= '<script type="text/javascript" src="https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML"></script>'

    )
    is_non_calculator: bool = Field(
        default=True,
        description="It indicates calculator not required for this question",
        example=True
    )
    min_time: int = Field(
        ...,
        description="The time must be an integer in seconds must be less than max_time",
        example=10
    )
    max_time: int = Field(
        ...,
        description="The time must be an integer in seconds must be less than end_time",
        example=20
    )
    end_time: int = Field(
        ...,
        description="The time must be an integer in seconds",
        example=30
    )
    learning_content: Optional[str] = Field(
        ...,
        description="The learning content should be html format",
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

    @validator('ln_id')
    def validate_ln_id(cls, value):
        try:
            ln_id = value + '-'
            if ln_id != cls.qt_id[:20]:
                raise ValueError("First 19 characters of ln_id and qt_id must be same")
        except Exception as e:
            raise ValueError(e)
        return value

    @validator('qual_dict')
    def validate_qual_dict(cls, value):
        if type(value) != list:
            raise ValueError("qualification dictionary must be a list with one or more dictionaries")
        qual_dict_ids = [item['qualification_id'] for item in value]
        if len(qual_dict_ids) != len(set(qual_dict_ids)):
            raise ValueError("qualification ids should not be same")
        for item in value:
            # if item['qualification_id'] is
            if item['qualification_title'] is None:
                raise ValueError("qualification_title should not empty")
            try:
                if item['qualification_organisation'] is not None:
                    for org, val in item['typical_mark'].items():
                        if org not in item['qualification_organisation']:
                            raise ValueError(f"organisation '{org}' not exists in qualification_organisation.")
                        if val != "correct/incorrect":
                            if not isinstance(val, int):
                                raise ValueError(
                                    f"typical marks of '{org}' should be 'integer' or 'correct/incorrect'.")
            except Exception as e:
                raise ValueError(str(e))
        return value

    @validator('repeatable_pattern')
    def validate_repeatable_pattern(cls, value):
        try:
            parts = value.split('|')
            cls.repeatable_length = len(parts)
            for i in parts:
                if not i.isdigit():
                    raise ValueError("The repeatable pattern should be integers with separation of '|' eg: '3|1|1' ")
        except Exception as e:
            raise ValueError(e)
        return value

    @validator('period_pattern')
    def validate_period_pattern(cls, value):
        try:
            if cls.repeatable_length == 1:
                if value is not None:
                    raise ValueError("The period pattern should be null.")
            if cls.repeatable_length > 1:
                if value is None:
                    raise ValueError("The period pattern should not be null.")
            if value is not None:
                parts = value.split('|')
                for i in parts:
                    if not i.isdigit():
                        raise ValueError("The period pattern should be integers with separation of '|' eg: '60|90' ")
                if len(parts) != cls.repeatable_length - 1:
                    raise ValueError(
                        "The period pattern length should less than repeatable pattern eg: '60|90'(repeatable pattern: '3|1|1') ")
        except Exception as e:
            raise ValueError(e)
        return value

    @validator('country_id')
    def validate_country_code(cls, value):
        if value is None or value == []:
            raise ValueError("Country id should not be empty")
        if value is not None:
            for i in value:
                if len(i) != 2 or not i.isupper():
                    raise ValueError(f"Country id '{i}' must be exactly 2 uppercase letters.")
                country_list = read_country_json(country_json)
                if i not in country_list:
                    raise ValueError(f"Country id '{i}' is not valid")
        return value

    @model_validator(mode='before')
    def validate_time(cls, data) -> Any:
        try:
            qt_format = data['qt_format']
            if qt_format not in ['match', 'blank', 'selection']:
                raise ValueError("qt_format must be 'match' or 'blank' or 'selection'.")
            min_time = data['min_time']
            max_time = data['max_time']
            end_time = data['end_time']
            if min_time>max_time:
                raise ValueError('min time must be less than max time and end time')
            if max_time>end_time:
                raise ValueError("max time must be greater than min time and less than end time")
        except Exception as e:
            raise ValueError(e)
        return data


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
    - parent_nodes (Optional[List[str]]): A comma-separated list of parent nodes.
      - Example: ['001a-001a-001a-001a-0001a','001a-001a-001a-001a-0002a']
      - Description: Optional field that can be empty or a comma-separated list.
    - qual_dict List(dict): A comma-separated list of dictionaries
      - Example: [
        {
            "qualification_id":  "000001",
            "qualification_title": "GCSE",
            "qualification_variations": ["Foundation","Higher"],
            "qualification_organisation": ["Edexcel", "AQA", "OCR", "CCEA", "WJEC"],
            "typical_mark": {
                "Edexcel": 4,
                "AQA": "correct/incorrect",
                "OCR": 3,
                "CCEA": 4,
                "WJEC": 4
            }
            "qualification_module": ["Pure Mathematics 1"],
            "qualification_study_level": "Key Stage 1",
            "qualification_grade": "U"
        },
        {
            "qualification_id":  "000002",
            "qualification_title": "GCSE",
            "qualification_variations": ["Foundation","Higher"],
            "qualification_organisation": ["Edexcel", "AQA", "OCR"],
            "typical_mark": {
                "Edexcel": 4,
                "AQA": 4,
                "OCR": 3
            }
            "qualification_module": ["Pure Mathematics 2"],
            "qualification_study_level": "Key Stage 2",
            "qualification_grade": "A"
        }
      ]
      - Description: The qualification dict with list of dictionaries one or more and qualification id should not be same.
    - qt_age conint(ge=1, le=100): The maximum order of the question type.
      - Example: 25
      - Description: The age must be an integer between 1 and 100 inclusive.
    - qt_format (str): The question format of question type.
      - Example: match
      - Description: Question format of question type. Must be one of "match", "blank", or "selection".
    - qt_order (int): The question type order value must less than max_order of learning network.
      - Example: 1
      - Description: Integer value.
    - repeatable_pattern (str): The repeatable pattern of question type.
      - Example: "3|1|1"
      - Description: The question type repeatable pattern in times .
    - period_pattern (str): The period for repeating question type.
      - Example: "60|90"
      - Description: The required days to repeat the question type.
    - country_id (List[str]): A comma-separated list of two-letter uppercase country code.
      - Example: ["GB", "IN"]
      - Description: The list of country codes must be a two-letter uppercase string.
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
      - Description: The time must be an integer in seconds must be less than max_time
    - max_time (int): Required maximum time for question
      - Example: 30
      - Description: The time must be an integer in seconds must be less than end_time
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
    parent_nodes: Optional[List[str]] = Field(
        default = None,
        description="An optional comma-separated list of parent nodes.",
        example=['001a-001a-001a-001a-0001a', '001a-001a-001a-001a-0002a']
    )
    qual_dict: List[dict] = Field(
        ...,
        example= [
            {
                "qualification_id": "000001",
                "qualification_title": "GCSE",
                "qualification_variations": ["Foundation", "Higher"],
                "qualification_organisation": ["Edexcel", "AQA", "OCR", "CCEA", "WJEC"],
                "typical_mark": {
                    "Edexcel": 4,
                    "AQA": "correct/incorrect",
                    "OCR": 3,
                    "CCEA": 4,
                    "WJEC": 4,
                },
                "qualification_module": ["Pure Mathematics 1"],
                "qualification_study_level": "Key Stage 1",
                "qualification_grade": "U"
            },
            {
                "qualification_id": "000002",
                "qualification_title": "GCSE",
                "qualification_variations": ["Foundation", "Higher"],
                "qualification_organisation": ["Edexcel", "AQA", "OCR"],
                "typical_mark": {
                    "Edexcel": 4,
                    "AQA": 4,
                    "OCR": 3
                },
                "qualification_module": ["Pure Mathematics 2"],
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
    qt_format: Literal["match", "blank", "selection"] = Field(
        ...,
        example='match',
        description="Question format of question type. Must be one of 'match', 'blank' or 'selection'."
    )
    qt_order: int = Field(
        ...,
        example=1,
        description="Integer value of question type order."
    )
    repeatable_pattern: str = Field(
        ...,
        description="The question type repeatable pattern in times.",
        example="3|1|1"
    )
    period_pattern: Optional[str] = Field(
        default = None,
        description="The required days to repeat the question type.",
        example="60|90"
    )
    country_id: List[str] = Field(
        ...,
        description="The list of country codes must be a two-letter uppercase string",
        example=["GB", "IN"]
    )
    page_script: Optional[str] = Field(
        default = None,
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
        description="The time must be an integer in seconds must be less than max_time",
        example=10
    )
    max_time: conint(ge=1) = Field(
        ...,
        description="The time must be an integer in seconds must be less than end_time",
        example=20
    )
    end_time: conint(ge=1) = Field(
        ...,
        description="The time must be an integer in seconds",
        example=30
    )
    learning_content: Optional[str] = Field(
        default = None,
        description="The learning content should be html format",
        example="<h1>Welcome</h1>"
    )

    @validator('qt_id', always=True)
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

    @validator('ln_id', always=True)
    def validate_ln_id(cls, value):
        try:
            ln_id = value + '-'
            if ln_id != cls.qt_id[:20]:
                raise ValueError("First 19 characters of ln_id and qt_id must be same")
        except Exception as e:
            raise ValueError(e)
        return value

    @validator('qual_dict', always=True)
    def validate_qual_dict(cls, value):
        if type(value) != list:
            raise ValueError("qualification dictionary must be a list with one or more dictionaries")
        qual_dict_ids = [item['qualification_id'] for item in value]
        if len(qual_dict_ids) != len(set(qual_dict_ids)):
            raise ValueError("qualification ids should not be same")
        for item in value:
            if item['qualification_title'] is None:
                raise ValueError("qualification_title should not empty")
            try:
                if item['qualification_organisation'] is not None:
                    for org, val in item['typical_mark'].items():
                        if org not in item['qualification_organisation']:
                            raise ValueError(f"organisation '{org}' not exists in qualification_organisation.")
                        if val != "correct/incorrect":
                            if not isinstance(val, int):
                                raise ValueError(f"typical marks of '{org}' should be 'integer' or 'correct/incorrect'.")
            except Exception as e:
                raise ValueError(str(e))
        return value

    @validator('repeatable_pattern', always=True)
    def validate_repeatable_pattern(cls, value):
        try:
            parts = value.split('|')
            cls.repeatable_length = len(parts)
            for i in parts:
                if not i.isdigit():
                    raise ValueError("The repeatable pattern should be integers with separation of '|' eg: '3|1|1' ")
        except Exception as e:
            raise ValueError(e)
        return value

    @validator('period_pattern', always=True)
    def validate_period_pattern(cls, value):
        try:
            if cls.repeatable_length == 1:
                if value is not None:
                    raise ValueError("The period pattern should be null.")
            if cls.repeatable_length > 1:
                if value is None:
                    raise ValueError("The period pattern should not be null.")
            if value is not None:
                parts = value.split('|')
                for i in parts:
                    if not i.isdigit():
                        raise ValueError("The period pattern should be integers with separation of '|' eg: '60|90' ")
                if len(parts) != cls.repeatable_length - 1:
                    raise ValueError(
                        "The period pattern length should less than repeatable pattern eg: '60|90'(repeatable pattern: '3|1|1') ")
        except Exception as e:
            raise ValueError(e)
        return value

    @validator('country_id', always=True)
    def validate_country_code(cls, value):
        if value is None or value == []:
            raise ValueError("Country id should not be empty")
        if value is not None:
            for i in value:
                if len(i) != 2 or not i.isupper():
                    raise ValueError(f"Country id '{i}' must be exactly 2 uppercase letters.")
                country_list = read_country_json(country_json)
                if i not in country_list:
                    raise ValueError(f"Country id '{i}' is not valid")
        return value

    @model_validator(mode='before')
    def validate_time(cls, data) -> Any:
        try:
            qt_format = data['qt_format']
            if qt_format not in ['match', 'blank', 'selection']:
                raise ValueError("qt_format must be 'match' or 'blank' or 'selection'.")
            min_time = data['min_time']
            max_time = data['max_time']
            end_time = data['end_time']
            if min_time > max_time:
                raise ValueError('min time must be less than max time and end time')
            if max_time > end_time:
                raise ValueError("max time must be greater than min time and less than end time")
        except Exception as e:
            raise ValueError(e)
        return data



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


