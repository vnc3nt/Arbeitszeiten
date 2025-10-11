from flask_restful import Resource
from api_resources.util import color_type, enum_type, format_data, int_or, token_param, unsigned_int, format_error
from database.models import Profile, WorkTimeFormat
from shared.constants import GET_LOCATIONS, PATCH_LOCATIONS, POST_LOCATIONS, HEADER_LOGIN_TOKEN
from shared.messages import MESSAGE_INVALID_ACCESS_TOKEN, MESSAGE_PROFILE_NOT_FOUND
from shared.login import get_user, is_valid_token
from shared.profiles import create_profile, delete_profile, get_all_user_profiles, get_last_viewed_user_profile, get_user_profile_by_id, update_user_profile
from flask_restful.inputs import boolean, date as flask_date



profile_create = token_param.copy()
profile_create.add_argument(
        name="name",
        type=str,
        required=True,
        nullable=False,
        location=POST_LOCATIONS,
        help="No profile name given"
)
profile_create.add_argument(
        name="color",
        type=color_type,
        nullable=False,
        required=True,
        location=POST_LOCATIONS,
        help="No color set"
)
profile_create.add_argument(
        name="work_start",
        type=flask_date,
        required=False,
        nullable=True,
        default=None,
        location=POST_LOCATIONS,
        help="No work begin set"
)
profile_create.add_argument(
        name="work_period",
        type=enum_type(WorkTimeFormat),
        required=True,
        nullable=False,
        location=POST_LOCATIONS,
        help="Whether the tracking should be in MONTHs or WEEKs"
)
profile_create.add_argument(
        name="work_time",
        type=unsigned_int,
        required=True,
        nullable=False,
        location=POST_LOCATIONS,
        help="The time someone needs/wants to work every period in hours"
)

profile_get = token_param.copy()
profile_get.add_argument(
        name="id",
        type=int_or("last"),
        nullable=True,
        required=False,
        location=GET_LOCATIONS,
        help="If not present, will return all user profiles. If 'last', will return the last viewed profile"
)
profile_get.add_argument(
    name="include_entries",
    type=boolean,
    nullable=False,
    required=False,
    default=False,
    location=GET_LOCATIONS,
    help="Whether the API should load all work entries or not"
)
profile_get.add_argument(
    name="include_work_periods",
    type=boolean,
    nullable=False,
    required=False,
    default=False,
    location=GET_LOCATIONS,
    help="Whether the API should load all work entries or not"
)
profile_get.add_argument(
    name="update_last_profile",
    type=boolean,
    nullable=False,
    required=False,
    default="true",
    location=GET_LOCATIONS,
    help="Whether to change the last opened profile in the database or not"
)

profile_patch = token_param.copy()
profile_patch.add_argument(
    name="id",
    type=int,
    nullable=False,
    required=True,
    location=PATCH_LOCATIONS,
    help="The id of the profile to change"
)
profile_patch.add_argument(
    name="name",
    type=str,
    nullable=False,
    required=False,
    location=PATCH_LOCATIONS,
    help="New name of the profile"
)
profile_patch.add_argument(
    name="color",
    type=color_type,
    nullable=False,
    required=False,
    location=PATCH_LOCATIONS,
    help="New color of the profile"
)

profile_delete = token_param.copy()
profile_delete.add_argument(
    name="id",
    type=int,
    nullable=False,
    required=True,
    location=PATCH_LOCATIONS,
    help="The id of the profile to delete"
)



class Profiles(Resource):
    def get(self):
        data = profile_get.parse_args()
        print(data)
        token = data[HEADER_LOGIN_TOKEN]
        if not is_valid_token(token):
            return format_error(MESSAGE_INVALID_ACCESS_TOKEN, 401)
        user = get_user(token)
        profile = None
        include_entries = data["include_entries"]
        include_work_periods = data["include_work_periods"]
        if data.get("id") is None:
            profile = get_all_user_profiles(user.id)
        elif data["id"] == "last":
            profile = get_last_viewed_user_profile(user.id)
        else:
            profile = get_user_profile_by_id(user.id, data["id"], data["update_last_profile"])

        if not profile:
            return format_error(MESSAGE_PROFILE_NOT_FOUND, 404)
        return format_data(
                profile.to_json(include_entries=include_entries, include_work_periods=include_work_periods)
                if isinstance(profile, Profile) else
                list(map(lambda x:x.to_json(include_entries=include_entries, include_work_periods=include_work_periods), profile))
        )

    def post(self):
        json = profile_create.parse_args()
        token = json[HEADER_LOGIN_TOKEN]
        if not is_valid_token(token):
            return format_error(MESSAGE_INVALID_ACCESS_TOKEN, 401)
        user = get_user(token)
        result = create_profile(user.id, json["name"], json["color"], json["work_start"], json["work_period"], json["work_time"])

        return format_data(result.value.to_json(), 201)

    def patch(self):
        data = profile_patch.parse_args()
        token = data[HEADER_LOGIN_TOKEN]
        if not is_valid_token(token):
            return format_error(MESSAGE_INVALID_ACCESS_TOKEN, 401)
        user = get_user(token)
        result = update_user_profile(user.id, data["id"], name=data["name"], color=data["color"])
        if result.is_error:
            return format_error(result.error, 409)
        return format_data(result.value.to_json(), 200)

    def delete(self):
        data = profile_patch.parse_args()
        token = data[HEADER_LOGIN_TOKEN]
        if not is_valid_token(token):
            return format_error(MESSAGE_INVALID_ACCESS_TOKEN, 401)
        user = get_user(token)
        success = delete_profile(user.id, data["id"])
        return {}, 204 if success else 404
        

