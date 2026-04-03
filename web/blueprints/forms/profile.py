from flask import Blueprint, request, flash, g, redirect, abort
from flask_babel import _

from database import WorkTimeFormat
from database.models import Users
from shared.constants import G_USER, FORM_PROFILE_NAME, FORM_PROFILE_COLOR, FORM_WORK_START, FORM_WORK_FORMAT, \
    FORM_WORK_TIME, FLASH_ERROR, FORM_PROFILE_ID
from shared.messages import MESSAGE_PROFILE_NOT_FOUND
from shared.profiles import create_profile, get_user_profile_by_name, get_user_profile_by_id, delete_profile
from shared.util import assert_non_null_values, assert_date, assert_enum, assert_color, assert_int
from web_util import switch_profile, clear_form_cache

profile_forms = Blueprint("profile", __name__, url_prefix="/dialog_bases")


@profile_forms.route("/create", methods=["POST"])
def create():
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


@profile_forms.route("/switch", methods=["POST"])
def switch():
    user: Users = g.get(G_USER)
    profile_id = request.form.get(FORM_PROFILE_ID)
    clear_form_cache()

    if profile_id is None:
        abort(400)

    profile_id = assert_int(profile_id)

    profile = get_user_profile_by_id(user.id, profile_id, update_last=True)
    if switch_profile(user.id, profile.id) is None:
        flash(MESSAGE_PROFILE_NOT_FOUND, FLASH_ERROR)

    return redirect(request.referrer)

@profile_forms.route("/delete", methods=["POST"])
def delete():
    user: Users = g.get(G_USER)
    profile_id = request.form.get(FORM_PROFILE_ID)
    clear_form_cache()

    if profile_id is None:
        abort(400)

    profile_id = assert_int(profile_id)
    delete_profile(user.id, profile_id)

    return redirect(request.referrer)
