from flask import Blueprint, request, flash, g, redirect, abort, session
from flask_babel import _

from database import WorkTimeFormat
from database.models import Users
from shared.constants import G_USER, FORM_PROFILE_NAME, FORM_PROFILE_COLOR, FORM_WORK_START, FORM_WORK_FORMAT, \
    FORM_WORK_TIME, FLASH_ERROR, FORM_PROFILE_ID, SESSION_TIMER_START, SESSION_TIMER_INTERVALS
from shared.messages import MESSAGE_PROFILE_NOT_FOUND
from shared.profiles import create_profile, get_user_profile_by_name, get_user_profile_by_id, delete_profile
from shared.util import assert_non_null_values, assert_date, assert_enum, assert_color, assert_int
from web_util import switch_profile, clear_form_cache, convert_utc_to_local_time
from datetime import datetime, timezone

timer = Blueprint("timer", __name__, url_prefix="/timer")

@timer.route("/begin", methods=["POST"])
def begin():
    session[SESSION_TIMER_START] = convert_utc_to_local_time(datetime.now(timezone.utc))
    if session.get(SESSION_TIMER_INTERVALS) is None:
        session[SESSION_TIMER_INTERVALS] = []
    return redirect(request.referrer)


@timer.route("/pause", methods=["POST"])
def pause():
    session[SESSION_TIMER_INTERVALS].append(
        (session[SESSION_TIMER_START], convert_utc_to_local_time(datetime.now(timezone.utc)))
    )
    session[SESSION_TIMER_START] = None
    return redirect(request.referrer)
