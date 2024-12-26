from pydantic import BaseModel, Field, EmailStr, constr, validator, conlist, conint,field_validator,model_validator
from typing import Optional, Dict, Union, List, Any, Literal
import re
from datetime import datetime

class School(BaseModel):
    """
    Request model for creating a new school.

    Attributes:
    - name (str): The name of the school.
      - Example: "Example High School"
      - Description: The name of the school to be created.
    - country_code (str): The country code of the school.
      - Example: "GB"
      - Description: The ISO 3166-1 alpha-2 country code where the school is located.
    - county_state (str): The name of the county or state where the school is located.
      - Example: "GB-WRL"
      - Description: The county or state where the school is situated, in the format of two uppercase letters followed by a hyphen and three to four uppercase letters.
    - identification_code (str): The identification code of the school.
      - Example: "SCH12345"
      - Description: The unique identification code assigned to the school.
    """

    name: constr(min_length=1) = Field(
        ...,
        description="The name of the school.",
        example="Example High School"
    )

    country_code: constr(min_length=2, max_length=2) = Field(
        ...,
        description="The country code of the school.",
        example="GB"
    )

    county_state: constr(min_length=2, max_length=7) = Field(
        ...,
        description="The name of the county or state where the school is located.",
        example="GB-WRL"
    )

    identification_code: constr(min_length=2, max_length=50) = Field(
        ...,
        description="The identification code of the school.",
        example="SCH12345"
    )

    @validator('country_code')
    def validate_country_code(cls, value):
        if not re.match(r'^[A-Z]{2}$', value):
            raise ValueError('Country code must be exactly 2 uppercase letters')
        return value

    @validator('county_state')
    def validate_county_state(cls, value):
        if value and not re.match(r'^[A-Z]{2}-[A-Z0-9]{0,4}$', value):
            raise ValueError(
                'County state must be in the format of two uppercase letters followed by a hyphen and three to four uppercase letters')
        return value

    # @validator('identification_code')
    # def validate_identification_code(cls, value):
    #     if not re.match(r'^[A-Z]{1,5}[0-9]{2,50}$', value):
    #         raise ValueError('Identification code must start with 1 to 5 uppercase letters followed by 2 to 50 digits')
    #     return value


class UpdateSchool(BaseModel):
    """
    Request model for updating an existing school.

    Attributes:
    - id (int): The unique identifier of the school to be updated.
      - Example: 1
      - Description: The ID of the school to be updated.
    - name (str, optional): The name of the school.
      - Example: "Updated High School"
      - Description: The new name of the school.
    - country (str, optional): The country code of the school.
      - Example: "GB"
      - Description: The ISO 3166-1 alpha-2 country code where the school is located.
    - county_state (str, optional): The name of the county or state where the school is located.
      - Example: "GB-LON"
      - Description: The new county or state where the school is situated.
    - identification_code (str, optional): The identification code of the school.
      - Example: "SCH54321"
      - Description: The new unique identification code assigned to the school.
    """
    id: int = Field(
        ...,
        description="The ID of the school to be updated.",
        example=1
    )
    name: constr(min_length=1) = Field(
        None,
        description="The name of the school.",
        example="Updated High School"
    )
    country: constr(min_length=2, max_length=2) = Field(
        None,
        description="The country code of the school.",
        example="GB"
    )
    county_state: constr(min_length=2, max_length=7) = Field(
        None,
        description="The name of the county or state where the school is located.",
        example="GB-LON"
    )
    identification_code: constr(min_length=2, max_length=50) = Field(
        None,
        description="The identification code of the school.",
        example="SCH54321"
    )

    @validator('country')
    def validate_country_code(cls, value):
        if not re.match(r'^[A-Z]{2}$', value):
            raise ValueError('Country code must be exactly 2 uppercase letters')
        return value

    @validator('county_state')
    def validate_county_state(cls, value):
        if value and not re.match(r'^[A-Z]{2}-[A-Z0-9]{0,4}$', value):
            raise ValueError(
                'County state must be in the format of two uppercase letters followed by a hyphen and three to four uppercase letters')
        return value

    # @validator('identification_code')
    # def validate_identification_code(cls, value):
    #     if not re.match(r'^[A-Z]{1,5}[0-9]{2,50}$', value):
    #         raise ValueError('Identification code must start with 1 to 5 uppercase letters followed by 2 to 50 digits')
    #     return value


class DeleteSchool(BaseModel):
    """
    Request model for deleting a school.

    Attributes:
    - school_id (int): The unique identifier of the school to delete.
      - Example: 1
      - Description: The ID of the school that needs to be deleted.
    """

    school_id: int = Field(
        ...,
        description="The unique identifier of the school that needs to be deleted.",
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
