import time
from datetime import timedelta

from flask import Blueprint, request, g, abort, render_template

from database.models import current_date
from shared.constants import ARGS_PERIOD_DATE, G_USER
from shared.login import redirect_to_login_when_logged_out
from shared.profiles import get_work_period
from shared.util import get_period_start, get_period_length, assert_date, try_datetime
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
        work_period = assert_date(work_period)
    work_time = get_work_period(profile.id, work_period)
    begin = get_period_start(work_period, work_time.workTimeFormat)
    end = work_period + get_period_length(work_period, work_time.workTimeFormat)
    previous = get_period_start(work_period - timedelta(days=1), work_time.workTimeFormat)
    return render_template(
        "htmx/stat_period.html",
        period=begin,
        previous=previous,
        entries=filter_work_times(user.id, profile.id, time_range=(begin, end)),
    )