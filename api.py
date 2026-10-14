from flask import Blueprint
from flask_restful import Api
from api_resources import (
    Apicheck,
    Data,
    Categories,
    CheckExistence,
    Profiles,
    ProfileSwitch,
)

app = Blueprint("api", __name__, url_prefix="/api")
api = Api(app)

api.add_resource(Apicheck, "/")
api.add_resource(Data, "/data", "/data/")
api.add_resource(Categories, "/categories", "/categories/", "/categories/<int:category_id>", "/categories/<int:category_id>/")
api.add_resource(CheckExistence, "/check-existence", "/check-existence/")
api.add_resource(
    Profiles,
    "/profiles",
    "/profiles/",
    "/profiles/<int:profile_id>",
    "/profiles/<int:profile_id>/",
)
api.add_resource(
    ProfileSwitch,
    "/profiles/<int:profile_id>/switch",
    "/profiles/<int:profile_id>/switch/",
)
