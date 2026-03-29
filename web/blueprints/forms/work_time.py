from flask import Blueprint, request, flash, g, redirect
from flask_babel import _

from shared.constants import G_USER, FLASH_ERROR, FORM_WORK_CATEGROY, FORM_WORK_BEGIN, FORM_WORK_END, FORM_WORK_NOTE
from shared.util import assert_non_null_values, assert_int, assert_datetime
from shared.work_time import add_new_work

work_time_forms = Blueprint("work_time", __name__, url_prefix="/dialog_bases")


@work_time_forms.route("/add", methods=["POST"], )
def add():
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
