from typing import Dict, Tuple
from flask_restful.reqparse import RequestParser

token_param = RequestParser()
token_param.add_argument(
    name="token",
    type=str,
    required=True,
    nullable=False,
    location="headers",
    help="Login token required")

def format_error(msg: str, code: int) -> Tuple[Dict, int]:
    return {"error": msg}, code


