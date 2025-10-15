
from flask_restful import Resource
from api_resources.util import color_type, enum_type, format_data, int_or, token_param, unsigned_int, format_error
from database.models import Profile, WorkTimeFormat
from shared.constants import DELETE_LOCATIONS, GET_LOCATIONS, PATCH_LOCATIONS, POST_LOCATIONS, HEADER_LOGIN_TOKEN
from shared.messages import MESSAGE_INVALID_ACCESS_TOKEN, MESSAGE_NO_WORK_TIME_FOUND, MESSAGE_PROFILE_NOT_FOUND
from shared.login import get_user, is_valid_token
from shared.profiles import create_profile, delete_profile, get_all_user_profiles, get_last_viewed_user_profile, get_user_profile_by_id, update_user_profile
from flask_restful.inputs import boolean, date as flask_date, iso8601interval as flask_timeinterval

from shared.work_time import add_new_work, filter_work_times


work_time_get = token_param.copy()
work_time_get.add_argument(
        name="id",
        type=int,
        required=False,
        nullable=False,
        location=GET_LOCATIONS,
        help="The id of an specific entry"
)
work_time_get.add_argument(
        name="profileId",
        type=int,
        required=False,
        nullable=False,
        location=GET_LOCATIONS,
        help="The id of the profile this work belongs to"
)
work_time_get.add_argument(
        name="categoryId",
        type=int,
        required=False,
        nullable=False,
        location=GET_LOCATIONS,
        help="The id of the category this work belongs to"
)
work_time_get.add_argument(
        name="timeRange",
        type=flask_timeinterval,
        required=False,
        nullable=False,
        location=GET_LOCATIONS,
        help="The time range to filter for"
)

new_work_time_entry = token_param.copy()
new_work_time_entry.add_argument(
        name="categoryId",
        type=int,
        required=True,
        nullable=False,
        location=POST_LOCATIONS,
        help="The id of the category this time is assigned to"
)
new_work_time_entry.add_argument(
        name="workTime",
        type=flask_timeinterval,
        required=True,
        nullable=False,
        location=POST_LOCATIONS,
        help="The time of the work as iso8601 interval"
)
new_work_time_entry.add_argument(
        name="note",
        type=str,
        required=False,
        nullable=False,
        default="",
        location=POST_LOCATIONS,
        help="The note of the time"
)


class WorkTime(Resource):
    def get(self):
        data = work_time_get.parse_args()
        token = data[HEADER_LOGIN_TOKEN]
        if not is_valid_token(token):
            return format_error(MESSAGE_INVALID_ACCESS_TOKEN, 401)
        user = get_user(token)
        print(data)
        work_times = filter_work_times(
                user.id,
                work_time_id=data.get("id"),
                profile_id=data.get("profileId"),
                category_id=data.get("categoryId"),
                time_range=data.get("timeRange")
        )
        if not work_times:
            return format_error(MESSAGE_NO_WORK_TIME_FOUND, 404)
        return format_data([
                x.to_json()
                for x in work_times
        ])



    def post(self):
        json = new_work_time_entry.parse_args()
        token = json[HEADER_LOGIN_TOKEN]
        if not is_valid_token(token):
            return format_error(MESSAGE_INVALID_ACCESS_TOKEN, 401)
        user = get_user(token)
        workStart, workEnd = json["workTime"]
        result = add_new_work(user.id, json["categoryId"], workStart, workEnd - workStart, json["note"])
        if result.is_error:
            return format_error(result.error, 409)
        return format_data(result.value.to_json(), 201)


