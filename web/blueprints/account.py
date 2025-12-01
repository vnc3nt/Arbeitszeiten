from flask import Blueprint, render_template, request, g, url_for, flash, redirect
from shared.util import assert_non_null_values
from shared.constants import SESSION_USER_TOKEN, FLASH_ERROR, G_USER
from shared.login import redirect_to_login_when_logged_out
from shared.profiles import get_last_viewed_user_profile
from flask_babel import _

account = Blueprint("account", __name__, url_prefix="/account")

account.before_request(redirect_to_login_when_logged_out)

@account.route("/home")
def home():
    user = g.get(G_USER)
    return render_template("home.html", profile=get_last_viewed_user_profile(user.id))