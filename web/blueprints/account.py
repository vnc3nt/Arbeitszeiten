from flask import Blueprint, render_template, request, g, url_for, flash, redirect
from shared.util import assert_non_null_values
from shared.constants import G_USER_TOKEN, FLASH_ERROR
from shared.login import redirect_to_login_when_logged_out
from flask_babel import _

account = Blueprint("account", __name__, url_prefix="/account")

account.before_request(redirect_to_login_when_logged_out)

@account.route("/home")
def home():
    return render_template("home.html")