from sqlalchemy import text
from datetime import timedelta
from flask import Blueprint, render_template, request, g, url_for, flash, redirect
from shared.util import assert_non_null_values, try_datetime, get_period_length, get_period_start
from shared.constants import SESSION_USER_TOKEN, FLASH_ERROR, G_USER, ARGS_DATE
from shared.login import redirect_to_login_when_logged_out
from shared.profiles import get_last_viewed_user_profile, get_categories, get_work_period
from shared.work_time import get_balance
from database.models import current_date, db
from flask_babel import _

account = Blueprint("account", __name__, url_prefix="/account")

account.before_request(redirect_to_login_when_logged_out)

@account.route("/home")
def home():
    user = g.get(G_USER)
    interval = try_datetime(request.args.get(ARGS_DATE), default=current_date())
    profile = get_last_viewed_user_profile(user.id)

    category_result = get_categories(user.id, profile.id if profile else None)
    if category_result.is_error:
        flash(_(category_result), category=FLASH_ERROR)
        categories = []
    else:
        categories = category_result.value

    opt = {}
    if profile:
        work_time = get_work_period(profile.id, interval)
        opt["worktime"] = work_time.workTime
        period = get_period_start(interval, work_time.workTimeFormat)

        # button control
        opt["prev_date"] = get_period_start(period - timedelta(days=1), work_time.workTimeFormat)
        opt["next_date"] = period + get_period_length(period, work_time.workTimeFormat)

        opt["total_work"] = get_balance(profile.id, period, opt["next_date"])


    return render_template(
        "home.html",
        profile=get_last_viewed_user_profile(user.id),
        categories=categories,
        **opt
    )


@account.route("/stats")
def stats():
    return "Not Implemented Yet"


@account.route("/profile")
def profile():
    return "Not Implemented Yet"


