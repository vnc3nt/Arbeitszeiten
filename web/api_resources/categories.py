from flask_restful import Resource
from api_resources.util import color_type, format_data, format_error, token_param
from database.models import ProfileCategory
from flask_restful.inputs import boolean

from shared.constants import DELETE_LOCATIONS, GET_LOCATIONS, HEADER_LOGIN_TOKEN, PATCH_LOCATIONS, POST_LOCATIONS
from shared.login import get_user, is_valid_token
from shared.messages import MESSAGE_CATEGORY_NOT_FOUND, MESSAGE_INVALID_ACCESS_TOKEN
from shared.profiles import create_category, delete_category, get_categories


category_create = token_param.copy()
category_create.add_argument(
        name="profileId",
        type=int,
        nullable=False,
        required=True,
        location=POST_LOCATIONS,
        help="The id of the dialog_bases this category shall belong to"
)
category_create.add_argument(
        name="name",
        type=str,
        nullable=False,
        required=True,
        location=POST_LOCATIONS,
        help="The name of the new category"
)
category_create.add_argument(
        name="color",
        type=color_type,
        nullable=False,
        required=True,
        location=POST_LOCATIONS,
        help="The color of the new category"
)

category_get = token_param.copy()
category_get.add_argument(
        name="profileId",
        type=int,
        nullable=False,
        required=False,
        location=GET_LOCATIONS,
        help="The dialog_bases id of the categories"
)
category_get.add_argument(
        name="id",
        type=int,
        nullable=False,
        required=False,
        location=GET_LOCATIONS,
        help="The category id"
)

category_patch = token_param.copy()
category_patch.add_argument(
        name="id",
        type=int,
        nullable=False,
        required=True,
        location=PATCH_LOCATIONS,
        help="the id of the category to modify"
)
category_patch.add_argument(
        name="name",
        type=str,
        nullable=False,
        required=False,
        location=PATCH_LOCATIONS,
        help="The name of the new category"
)
category_patch.add_argument(
        name="color",
        type=color_type,
        nullable=False,
        required=False,
        location=PATCH_LOCATIONS,
        help="The color of the new category"
)
category_delete = token_param.copy()
category_delete.add_argument(
        name="id",
        type=int,
        nullable=False,
        required=True,
        location=DELETE_LOCATIONS,
        help="The id of the dialog_bases to delete"
)


class Categories(Resource):
    def get(self):
        data = category_get.parse_args()
        token = data[HEADER_LOGIN_TOKEN]
        if not is_valid_token(token):
            return format_error(MESSAGE_INVALID_ACCESS_TOKEN, 401)
        user = get_user(token)
        result = get_categories(user.id, data.get("profileId"), data.get("id"))
        if result.is_error:
            return format_error(result.error, 409)
        return format_data([
                x.to_json(include_profile_id=True)
                for x in result.value],
                200
        )

    def post(self):
        json = category_create.parse_args()
        token = json[HEADER_LOGIN_TOKEN]
        if not is_valid_token(token):
            return format_error(MESSAGE_INVALID_ACCESS_TOKEN, 401)
        user = get_user(token)
        result = create_category(user.id, json["profileId"], json["name"], json["color"])
        if result.is_error:
            return format_error(result.error, 409)
        return format_data(result.value.to_json(include_profile_id=True), 200)

    def patch(self):
        data = category_create.parse_args()
        token = data[HEADER_LOGIN_TOKEN]
        if not is_valid_token(token):
            return format_error(MESSAGE_INVALID_ACCESS_TOKEN, 401)
        user = get_user(token)
        result = update_category(user.id, data["id"], name=data["name"], color=data["color"])
        if result.is_error:
            return format_error(result.error, 409)
        return format_data(result.value.to_json(), 200)


    def delete(self):
        data = category_delete.parse_args()
        token = data[HEADER_LOGIN_TOKEN]
        if not is_valid_token(token):
            return format_error(MESSAGE_INVALID_ACCESS_TOKEN, 401)
        user = get_user(token)
        success = delete_category(user.id, data["id"])
        return ({}, 204) if success else format_error(MESSAGE_CATEGORY_NOT_FOUND, 404)

