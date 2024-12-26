from typing import Literal, Optional, Dict, Union, List,Any
from pydantic import BaseModel,  Field, EmailStr, constr, validator, conlist, conint,field_validator,model_validator


class Question_gen(BaseModel):
    qt_id: str = Field(
        ...,
        example="001a-001a-001a-001a-0001a",
        description="The qt_id to generate questions"
    )
    q_numb_to_generate: int = Field(
        ...,
        example= 3,
        description="The required number of questions to generate"
    )
    q_var_to_generate : int = Field(
        ...,
        example = 1,
        description="The variation that has to generate."
    )
    action_code: Literal[0,1] = Field(
        ...,
        description="Value '0' for writing to database, '1' for html generation",
        example=1
    )
    qt_format: Literal["match", "blank", "selection"] = Field(
        ...,
        example='match',
        description="Question format of question type. Must be one of 'match', 'blank' or 'selection'."
    )
    current_q_num: dict = Field(
        ...,
        example ={
            "1":20,
            "2":10
        },
        description="Current number of questions for different variations"
    )


class QuestionGeneration(BaseModel):
    qt_id: str = Field(
        ...,
        example="001a-001a-001a-001a-0001a",
        description="The qt_id to generate questions"
    )
    q_numb_to_generate: int = Field(
        ...,
        example= 3,
        description="The required number of questions to generate"
    )
    q_var_to_generate: int = Field(
        ...,
        example=1,
        description="The variation that has to generate."
    )
    action_code: Literal[0, 1] = Field(
        ...,
        description="Value '0' for writing to database, '1' for html generation",
        example=1
    )
    qt_format: Literal["match", "blank", "selection"] = Field(
        ...,
        example='match',
        description="Question format of question type. Must be one of 'match', 'blank' or 'selection'."
    )
    current_q_num: dict = Field(
        ...,
        example ={
            "1":20,
            "2":10
        },
        description="Current number of questions for different variations"
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


