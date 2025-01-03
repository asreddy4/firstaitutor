from pydantic import BaseModel, Field, EmailStr, constr, validator, conlist, conint,field_validator,model_validator
from typing import Optional, Dict, Union, List, Any, Literal
import re
from datetime import datetime

class Subject(BaseModel):
    """
    Model for representing a subject.

    Attributes:
    - name (str): The name of the subject.
      - Example: "mathematics", "geometry", "physics"
      - Description: The name of the subject (e.g., mathematics, geometry, physics).
    - subject_id (str): The unique identifier for the subject.
      - Format: '001a', '002b', etc.
      - Description: The unique identifier for the subject with the format 'XXXy', where X is a digit and y is a letter.
    """

    name: constr(min_length=2, max_length=100) = Field(
        ...,
        example="mathematics",
        description="The name of the subject (e.g., mathematics, geometry, physics)."
    )

    subject_id: str = Field(
        ...,
        example="001a",
        description="The unique identifier for the subject with the format 'XXXy', where X is a digit and y is a lowercase letter."
    )

    @validator('subject_id')
    def validate_subject_id_format(cls, subject_id):
        if len(subject_id) != 4:
            raise ValueError("subject_id must be exactly 4 characters long.")
        if not subject_id[:3].isdigit():
            raise ValueError("The first three characters of subject_id must be digits.")
        if not subject_id[3].islower():
            raise ValueError("The last character of subject_id must be a lowercase letter.")
        return subject_id


class UpdateSubject(BaseModel):
    """
    Request model for updating a subject.

    Attributes:
    - id (int): The ID of the subject to update.
    - new_name (str): The new name of the subject.
    - subject_id (str): The unique identifier for the subject.
      - Format: '001a', '002b', etc.
      - Description: The unique identifier for the subject with the format 'XXXy', where X is a digit and y is a letter.
    """
    id: int = Field(example=1, description="The ID of the subject to update.")
    new_name: constr(min_length=2, max_length=100) = Field(default=None, example="Mathematics",
                                                           description="The new name of the subject.")
    subject_id: str = Field(
        ...,
        example="001a",
        description="The unique identifier for the subject with the format 'XXXy', where X is a digit and y is a lowercase letter."
    )

    @validator('subject_id')
    def validate_subject_id_format(cls, subject_id):
        if len(subject_id) != 4:
            raise ValueError("subject_id must be exactly 4 characters long.")
        if not subject_id[:3].isdigit():
            raise ValueError("The first three characters of subject_id must be digits.")
        if not subject_id[3].islower():
            raise ValueError("The last character of subject_id must be a lowercase letter.")
        return subject_id


class DeleteSubject(BaseModel):
    """
    Request model for deleting a subject.

    Attributes:
    - subject_id (str): The ID of the subject to delete.
    """
    subject_id: str = Field(
        ...,
        example="001a",
        description="The unique identifier for the subject with the format 'XXXy', where X is a digit and y is a lowercase letter."
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


