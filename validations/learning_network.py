from pydantic import BaseModel, Field, EmailStr, constr, validator, conlist, conint,field_validator,model_validator
from typing import Optional, Dict, Union, List,Any
from datetime import date
from typing import Literal
import re
from datetime import datetime
from pydantic_core.core_schema import FieldValidationInfo

class LearningNetwork(BaseModel):
    """
    Data model for the Learning Network table.

    Attributes:
    - ln_id (str): The unique identifier for the qualification based on node types.
      - Example: "001a-001a-001a-001a"
      - Description: Format of 'ln_id' depends on 'is_keynode' and 'is_subject_head_node'.
    - title (str): The title of the qualification.
      - Example: "Mathematics"
      - Description: The title must be a non-empty string.
    - subject_id (str): The unique identifier for the subject.
      - Format: '001a', '002b', etc.
      - Description: The unique identifier for the subject with the format 'XXXy', where X is a digit and y is a letter.
    - parent_nodes (Optional[str]): A comma-separated list of parent nodes.
      - Example: "001a-001a"
      - Description: Optional field that can be empty or a comma-separated list.
    - max_order (Optional[int]): The maximum order of the qualification.
      - Example: 5
      - Description: Optional integer value.
    - back_learning_level (Optional[int]): The back learning level of the qualification.
      - Example: 2
      - Description: Optional integer value.
    - is_subject_head_node (bool): Indicates if the qualification is a subject head node.
      - Example: False
      - Description: A boolean indicating whether the qualification is a subject head node.
    - is_keynode (bool): Indicates if the qualification is a key node.
      - Example: True
      - Description: A boolean indicating whether the qualification is a key node.
    - support_url (Optional[str]): A URL providing support or additional information.
      - Example: "https://example.com/support"
      - Description: Optional URL string.
    """


    ln_id: str = Field(
        ...,
        description="The unique identifier based on node types.",
        example="001a-001a-001a-001a"
    )
    title: str = Field(
        ...,
        description="The title must be a non-empty string.",
        example="Mathematics"
    )
    subject_id: str = Field(
        ...,
        example="001a",
        description="The unique identifier for the subject with the format 'XXXy', where X is a digit and y is a lowercase letter."
    )
    parent_nodes: Optional[List[str]] = Field(
        default=None,
        description="An optional comma-separated list of parent nodes.",
        example=['001a-001a','001a-002a']
    )
    max_order: int = Field(
        default=None,
        description="An optional integer representing the maximum order.",
        example=5
    )
    back_learning_level: int = Field(
        default=None,
        description="An optional integer representing the back learning level.",
        example=2
    )
    is_subject_head_node: bool = Field(
        default=False,
        description="Indicates if the qualification is a subject head node.",
        example=False
    )
    is_keynode: bool = Field(
        default=False,
        description="Indicates if the qualification is a key node.",
        example=True
    )
    support_url: str = Field(
        default=None,
        description="An optional URL providing support or additional information.",
        example="https://example.com/support"
    )

    @model_validator(mode='before')
    def validate_ln_id(cls, data) -> Any:
        value = str(data['ln_id'])
        subject_id = str(data['subject_id'])
        is_keynode = bool(data['is_keynode'])
        is_subject_head_node = bool(data['is_subject_head_node'])
        if is_keynode and is_subject_head_node:
            raise ValueError("Both 'is_keynode' and 'is_subject_head_node' cannot be True at the same time.")

        try:
            parts = value.split('-')
        except Exception as e:
            raise ValueError(e)
        for i in parts:

            if len(i) != 4:
                raise ValueError("id must be exactly 4 characters long.")
            if not i[:3].isdigit():
                raise ValueError("The first three characters of id must be digits.")
            if not i[3].islower():
                raise ValueError("The last character of id must be a lowercase letter.")
        if is_keynode:
            if not (len(parts) == 3):
                raise ValueError("For 'is_keynode' True, 'ln_id' should follow the format 'xxxx-xxxx-xxxx'.")
        elif is_subject_head_node:
            if not (len(parts) == 2):
                raise ValueError("For 'is_subject_head_node' True, 'ln_id' should follow the format 'xxxx-xxxx'.")
        else:
            if not (len(parts) == 4):
                raise ValueError(
                    "For both 'is_keynode' and 'is_subject_head_node' False, 'ln_id' should follow the format 'xxxx-xxxx-xxxx-xxxx'.")

        if subject_id is not None:
        # Ensure the first 4 characters of ln_id match subject_id
            if len(subject_id) != 4:
                raise ValueError("s_id must be exactly 4 characters long.")
            if not subject_id[:3].isdigit():
                raise ValueError("The first three characters of s_id must be digits.")
            if not subject_id[3].islower():
                raise ValueError("The last character of s_id must be a lowercase letter.")
            if value[0:4] != subject_id:
                raise ValueError(
                    f"First four characters of 'ln_id' must match the zero-padded 'subject_id'. Expected prefix '{subject_id}'.")
        back_learning = data['back_learning_level']
        max_order = data['max_order']
        if back_learning > max_order:
             raise ValueError('back_learning_level number must be less than or equal to max')
        return data


class DeleteLearningNetwork(BaseModel):
    """
    Request model for deleting a learning_network.

    Attributes:
    - id (int): The unique identifier of the learning_network to delete.
      - Example: 1
      - Description: The ID of the learning_network that needs to be deleted.
    """

    id: int = Field(
        ...,
        description="The unique identifier of the learning_network that needs to be deleted.",
        example=1
    )


class UpdateLearningNetwork(BaseModel):
    """
    Data model for the Learning Network table.

    Attributes:
        - id (int): The unique identifier of the learning_network to be updated.
      - Example: 1
      - Description: The ID must be a positive integer representing the unique identifier of the learning_network to be updated.
    - ln_id (str): The unique identifier for the qualification based on node types.
      - Example: "001a-001a-001a-001a"
      - Description: Format of 'ln_id' depends on 'is_keynode' and 'is_subject_head_node'.
    - title (str): The title of the qualification.
      - Example: "Mathematics"
      - Description: The title must be a non-empty string.
    - subject_id (int): An integer identifier for the subject.
      - Example: 123
      - Description: The subject ID must be an integer and cannot be empty.
    - parent_nodes (Optional[str]): A comma-separated list of parent nodes.
      - Example: "001a-001a"
      - Description: Optional field that can be empty or a comma-separated list.
    - max_order (Optional[int]): The maximum order of the qualification.
      - Example: 5
      - Description: Optional integer value.
    - back_learning_level (Optional[int]): The back learning level of the qualification.
      - Example: 2
      - Description: Optional integer value.
    - is_subject_head_node (bool): Indicates if the qualification is a subject head node.
      - Example: False
      - Description: A boolean indicating whether the qualification is a subject head node.
    - is_keynode (bool): Indicates if the qualification is a key node.
      - Example: True
      - Description: A boolean indicating whether the qualification is a key node.
    - support_url (Optional[str]): A URL providing support or additional information.
      - Example: "https://example.com/support"
      - Description: Optional URL string.
    """

    id: int = Field(
        ...,
        description="The ID must be a positive integer representing the unique identifier of the learning_network to be updated.",
        example=1
    )
    ln_id: str = Field(
        ...,
        description="The unique identifier based on node types.",
        example="001a-001a-001a-001a"
    )
    title: str = Field(
        ...,
        description="The title must be a non-empty string.",
        example="Mathematics"
    )
    subject_id: str = Field(
        ...,
        description="The subject ID must be an integer and cannot be empty.",
        example="001a"
    )
    parent_nodes: Optional[List[str]] = Field(
        default=None,
        description="An optional comma-separated list of parent nodes.",
        example=['001a-001a', '001a-002a']
    )
    max_order: int = Field(
        default=None,
        description="An optional integer representing the maximum order.",
        example=5
    )
    back_learning_level: int = Field(
        default=None,
        description="An optional integer representing the back learning level.",
        example=2
    )
    is_subject_head_node: bool = Field(
        default=False,
        description="Indicates if the qualification is a subject head node.",
        example=False
    )
    is_keynode: bool = Field(
        default=False,
        description="Indicates if the qualification is a key node.",
        example=True
    )
    support_url: str = Field(
        default=None,
        description="An optional URL providing support or additional information.",
        example="https://example.com/support"
    )

    @model_validator(mode='before')
    def validate_ln_id(cls, data) -> Any:
        value = str(data['ln_id'])
        subject_id = str(data['subject_id'])
        is_keynode = bool(data['is_keynode'])
        is_subject_head_node = bool(data['is_subject_head_node'])
        if is_keynode and is_subject_head_node:
            raise ValueError("Both 'is_keynode' and 'is_subject_head_node' cannot be True at the same time.")

        try:
            parts = value.split('-')
        except Exception as e:
            raise ValueError(e)
        for i in parts:

            if len(i) != 4:
                raise ValueError("id must be exactly 4 characters long.")
            if not i[:3].isdigit():
                raise ValueError("The first three characters of id must be digits.")
            if not i[3].islower():
                raise ValueError("The last character of id must be a lowercase letter.")
        if is_keynode:
            if not (len(parts) == 3):
                raise ValueError("For 'is_keynode' True, 'ln_id' should follow the format 'xxxx-xxxx-xxxx'.")
        elif is_subject_head_node:
            if not (len(parts) == 2):
                raise ValueError("For 'is_subject_head_node' True, 'ln_id' should follow the format 'xxxx-xxxx'.")
        else:
            if not (len(parts) == 4):
                raise ValueError(
                    "For both 'is_keynode' and 'is_subject_head_node' False, 'ln_id' should follow the format 'xxxx-xxxx-xxxx-xxxx'.")

        if subject_id is not None:
            # Ensure the first 4 characters of ln_id match subject_id
            if len(subject_id) != 4:
                raise ValueError("s_id must be exactly 4 characters long.")
            if not subject_id[:3].isdigit():
                raise ValueError("The first three characters of s_id must be digits.")
            if not subject_id[3].islower():
                raise ValueError("The last character of s_id must be a lowercase letter.")
            if value[0:4] != subject_id:
                raise ValueError(
                    f"First four characters of 'ln_id' must match the zero-padded 'subject_id'. Expected prefix '{subject_id}'.")
        back_learning = data['back_learning_level']
        max_order = data['max_order']
        if back_learning > max_order:
            raise ValueError('back_learning_level number must be less than or equal to max')
        return data

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


