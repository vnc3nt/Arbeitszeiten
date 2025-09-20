from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from models import users

post_arguments = RequestParser()
post_arguments.add_argument(
    name="type",
    type=str,
    nullable=False,
    required=True,
)

post_arguments.add_argument(
    name="value",
    type=str,
    nullable=False,
    required=True,
)


class CheckExistence(Resource):
    def post(self):
        data = post_arguments.parse_args(strict=True)

        if data["type"] == "username":
            result = users.query.filter_by(username=data["value"]).first()

        else:
            return {}, 400
        return {"exists": result is not None}, 200
