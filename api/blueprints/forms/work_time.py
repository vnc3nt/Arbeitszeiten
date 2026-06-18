from flask import Blueprint, request, flash, g, redirect, session
from flask_babel import _

from shared.constants import G_USER, FLASH_ERROR, FORM_WORK_CATEGORY, FORM_WORK_BEGIN, FORM_WORK_END, FORM_WORK_NOTE, \
    FORM_IS_TIMER, SESSION_TIMER_INTERVALS
from shared.util import assert_non_null_values, assert_int, assert_datetime
from shared.work_time import add_new_work

work_time_forms = Blueprint("work_time", __name__, url_prefix="/work-time")


@work_time_forms.route("/add", methods=["POST"], )
def add():
    user = g.get(G_USER)
    category = request.form.get(FORM_WORK_CATEGORY)
    start = request.form.get(FORM_WORK_BEGIN)
    end = request.form.get(FORM_WORK_END)
    note = request.form.get(FORM_WORK_NOTE, "")
    is_timer = request.form.get(FORM_IS_TIMER)
    assert_non_null_values(category, start, end)

    category = assert_int(category)
    start = assert_datetime(start, format="%Y-%m-%dT%H:%M")
    end = assert_datetime(end, format="%Y-%m-%dT%H:%M")

    result = add_new_work(user.id, category, start, end - start, note)
    if result.is_error:
        flash(_(result.error), category=FLASH_ERROR)
    elif is_timer is not None:
        session[SESSION_TIMER_INTERVALS] = session[SESSION_TIMER_INTERVALS][1:]
    return redirect(request.referrer)
