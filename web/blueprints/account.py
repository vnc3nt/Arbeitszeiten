from datetime import timedelta

from flask import Blueprint, render_template, request, g, flash, abort, session
from flask_babel import _

from database.models import current_date
from shared.constants import FLASH_ERROR, G_USER, ARGS_DATE, SESSION_TIMEZONE_OFFSET, FORM_TIMEZONE_OFFSET
from shared.login import redirect_to_login_when_logged_out
from shared.profiles import get_last_viewed_user_profile, get_categories, get_work_period, get_user_profiles, \
    get_user_profile_by_id
from shared.util import try_datetime, get_period_length, get_period_start, assert_int
from shared.work_time import filter_work_times, get_balance
from web_util import get_current_profile

account = Blueprint("account", __name__, url_prefix="/account")

account.before_request(redirect_to_login_when_logged_out)

@account.route("/home")
def home():
    user = g.get(G_USER)
    interval = try_datetime(request.args.get(ARGS_DATE), default=current_date())
    profile = get_current_profile(user.id)

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
        "page/home.html",
        profile=profile,
        categories=categories,
        **opt
    )


@account.route("/stats")
def stats():
    user = g.get(G_USER)
    profile = get_current_profile(user.id)
    entries = filter_work_times(user.id, profile.id)

    return render_template(
        "page/stats.html",
        profile=profile,
        entries=entries
    )


@account.route("/dialog_bases")
def profile_web():
    user = g.get(G_USER)
    profiles = get_user_profiles(user.id)
    return render_template(
        "page/profile.html",
        profiles=profiles,
        active_profile=get_current_profile(user.id)
    )


@account.route("/edit-profile/<int:profile_id>")
def edit_profile_web(profile_id: int):
    user = g.get(G_USER)
    profile = get_user_profile_by_id(user.id, profile_id)
    if profile is None:
        abort(404)
    return render_template("dialog/edit_profile.html", profile=profile)

@account.route("/timezone", methods=["patch"])
def update_timezone():
    offset = request.json.get(FORM_TIMEZONE_OFFSET)
    offset = assert_int(offset)
    session[SESSION_TIMEZONE_OFFSET] = offset
    return "", 204