from flask import Blueprint, request, redirect, g, flash, session, abort
from shared.constants import FORM_WORK_BEGIN, FORM_WORK_CATEGROY, FORM_WORK_END, G_USER, FORM_PROFILE_NAME, FORM_PROFILE_COLOR, FORM_WORK_FORMAT, FORM_WORK_START, FORM_WORK_TIME, FLASH_ERROR, SESSION_FORM_DATA, FORM_WORK_NOTE
from shared.login import redirect_to_login_when_logged_out
from shared.messages import MESSAGE_PROFILE_NOT_FOUND
from shared.util import assert_int, assert_non_null_values, assert_datetime, assert_enum, assert_color, assert_date
from shared.profiles import create_profile, get_categories, get_user_profile_by_name
from database.models import WorkTimeFormat, Users
from datetime import timedelta
from flask_babel import _
from web_util import switch_profile

from shared.work_time import add_new_work

forms = Blueprint("form", __name__, url_prefix="/form")
forms.before_request(redirect_to_login_when_logged_out)
@forms.before_request
def before_request():
    session[SESSION_FORM_DATA] = dict(request.form)

@forms.errorhandler(404)
def error404(error):
    return "Please use our website without programs"

@forms.errorhandler(400)
def error400(error):
    return "Please use our API instead"

@forms.route("/create-profile", methods=["POST"])
def create_profile_web():
    user = g.get(G_USER)
    name = request.form.get(FORM_PROFILE_NAME)
    color = request.form.get(FORM_PROFILE_COLOR)
    work_start = request.form.get(FORM_WORK_START)
    work_format = request.form.get(FORM_WORK_FORMAT)
    work_time = request.form.get(FORM_WORK_TIME)

    assert_non_null_values(name, color, work_start, work_format, work_time)
    work_start = assert_date(work_start)
    work_format = assert_enum(WorkTimeFormat, work_format)
    color = assert_color(color)
    result = create_profile(user.id, name, color, work_start, work_format, work_time)
    if result.is_error:
        flash(_(result.error), category=FLASH_ERROR)
    return redirect(request.referrer)


@forms.route("/switch-profile", methods=["POST"])
def switch_profile_web():
    user: Users = g.get(G_USER)
    profile_name = request.form.get(FORM_PROFILE_NAME)
    if profile_name is None:
        abort(400)

    profile = get_user_profile_by_name(user.id, profile_name)
    if switch_profile(user.id, profile.id) is None:
        flash(MESSAGE_PROFILE_NOT_FOUND, FLASH_ERROR)

    return redirect(request.referrer)

@forms.route("/add-work-time", methods=["POST"])
def add_work_time_web():
    user = g.get(G_USER)
    category = request.form.get(FORM_WORK_CATEGROY)
    start = request.form.get(FORM_WORK_BEGIN)
    end = request.form.get(FORM_WORK_END)
    note = request.form.get(FORM_WORK_NOTE, "")
    assert_non_null_values(category, start, end)

    category = assert_int(category)
    start = assert_datetime(start)
    end = assert_datetime(end)

    result = add_new_work(user.id, category, start, end - start, note)
    if result.is_error:
        flash(_(result.error), category=FLASH_ERROR)
    return redirect(request.referrer)
