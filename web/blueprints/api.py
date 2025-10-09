from flask import Blueprint
from flask_restful import Api
from api_resources import Apicheck
from api_resources.auth import Authentication

app = Blueprint("api", __name__, url_prefix="/api")
api = Api(app)

api.add_resource(Apicheck, "/")
api.add_resource(Authentication, "/auth/<string:auth_type>", "/auth/<string:auth_type>/")
