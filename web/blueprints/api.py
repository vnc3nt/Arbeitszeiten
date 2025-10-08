from flask import Blueprint
from flask_restful import Api
from api_resources import Apicheck, Data, Categories, CheckExistence

app = Blueprint("api", __name__, url_prefix="/api")
api = Api(app)

api.add_resource(Apicheck, "/")
