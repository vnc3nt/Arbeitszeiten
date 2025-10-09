from flask import abort
from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from shared.constants import AUTH_TYPE_LOGIN, AUTH_TYPE_REGISTER, POST_LOCATIONS
from api_resources.util import format_error
from shared.login import login_user, register_user


# register user account
register_values = RequestParser()
register_values.add_argument(
        name="username",
        type=str,
        required=True,
        nullable=False,
        location=POST_LOCATIONS,
        help="No username given"
)
register_values.add_argument(
        name="password",
        type=str,
        required=True,
        nullable=False,
        location=POST_LOCATIONS,
        help="No password given"
)
register_values.add_argument(
        name="confirm_password",
        type=str,
        required=True,
        nullable=False,
        location=POST_LOCATIONS,
        help="Password needs to be confirmed"
)


login_credentials = RequestParser()
login_credentials.add_argument(name="username",
                               type=str,
                               required=True,
                               nullable=False,
                               location=POST_LOCATIONS,
                               help="No username given")
login_credentials.add_argument(name="password",
                               type=str,
                               required=True,
                               nullable=False,
                               location=POST_LOCATIONS,
                               help="No password given")


class Authentication(Resource):
    def post(self, auth_type: str):
        if auth_type == AUTH_TYPE_REGISTER:
            return self.register()
        elif auth_type == AUTH_TYPE_LOGIN:
            return self.login()
        abort(404)

    def register(self):
        json = register_values.parse_args()
        error_message = register_user(json["username"], json["password"], json["confirm_password"])
        if error_message is None:
            return {}, 201
        return format_error(error_message, 400)

    def login(self):
        json = login_credentials.parse_args()
        error_message = login_user(json["username"], json["password"])
        if error_message.is_error:
            return format_error(error_message.value, 403)
        return {"token": error_message.value}

