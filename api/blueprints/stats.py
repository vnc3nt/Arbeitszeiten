from datetime import timedelta, datetime, time

from flask import Blueprint, request, g, abort, render_template

from database.models import current_date
from shared.constants import ARGS_PERIOD_DATE, G_USER, FORMAT_HTML_DATETIME
from shared.login import redirect_to_login_when_logged_out
from shared.profiles import get_work_period, get_work_begin
from shared.util import get_period_start, get_period_length, assert_date, try_datetime, assert_datetime
from shared.work_time import filter_work_times
from web_util import get_current_profile

stats = Blueprint("stats", __name__, url_prefix="/stats")
stats.before_request(redirect_to_login_when_logged_out)

@stats.route("/period")
def period():
    user = g.get(G_USER)
    profile = get_current_profile(user.id)
    if profile is None:
        abort(403)

    work_period = request.args.get(ARGS_PERIOD_DATE)
    if work_period is None:
        work_period = current_date()
    else:
        work_period = assert_datetime(work_period)

    work_time = get_work_period(profile.id, work_period)
    begin = get_period_start(work_period, work_time.workTimeFormat)
    end = work_period + get_period_length(work_period, work_time.workTimeFormat)
    previous = get_period_start(begin - timedelta(days=1), work_time.workTimeFormat)
    work_begin = get_work_begin(user.id, profile.id).workStart

    if work_begin > previous:
        return "", 204

    return render_template(
        "htmx/stat_period.html",
        period=begin,
        previous=previous.strftime(FORMAT_HTML_DATETIME),
        work_begin=work_begin,
        entries=filter_work_times(user.id, profile.id, time_range=(datetime.combine(begin, time.min), end)),
    )