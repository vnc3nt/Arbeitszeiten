from enum import Enum, EnumType
from typing import Any, Dict, Tuple
from flask_restful.reqparse import RequestParser

from shared.constants import COLOR_REGEX, HEADER_LOGIN_TOKEN

token_param = RequestParser()
token_param.add_argument(
    name=HEADER_LOGIN_TOKEN,
    type=str,
    required=True,
    nullable=False,
    location="headers",
    help="Login token required")

def format_error(msg: Any, code: int) -> Tuple[Dict, int]:
    return {"error": msg}, code

def format_data(data: Any, code: int = 200) -> Tuple[Dict, int]:
    return {"data": data}, code

def color_type(value):
    if len(value) == 7:
        return color_type(value[1:])
    if COLOR_REGEX.fullmatch(value) is None:
        raise ValueError("invalid color code")
    return value

def unsigned_int(value):
    i = int(value)
    if i < 0:
        raise ValueError("number has to be positive")
    return i

def enum_type(enum: EnumType):
    def type_constructor(value):
        if value not in enum._member_names_:
            raise ValueError("invalid choice:", value)
        return getattr(enum, value)
    return type_constructor


def int_or(*options: str):
    def t(value):
        if value in options:
            return value
        return int(value)
    return t
