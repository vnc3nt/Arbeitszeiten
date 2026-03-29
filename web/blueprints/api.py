from flask import Blueprint
from flask_restful import Api
from api_resources import Apicheck, Authentication, Profiles, Categories, WorkTime

app = Blueprint("api", __name__, url_prefix="/api")
api = Api(app)

api.add_resource(Apicheck, "/")
api.add_resource(Authentication, "/auth/<string:auth_type>", "/auth/<string:auth_type>/")
api.add_resource(Profiles, "/dialog_bases", "/dialog_bases/")
api.add_resource(Categories, "/category", "/category/")
api.add_resource(WorkTime, "/work", "/work/")
