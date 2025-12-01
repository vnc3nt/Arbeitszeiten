from flask import Blueprint, render_template, request, g, url_for, flash, redirect, session
from shared.util import assert_non_null_values
from shared.login import login_user, register_user, logout
from shared.constants import SESSION_USER_TOKEN, FORM_USERNAME, FORM_PASSWORD, FORM_CONFIRM_PASSWORD, FLASH_ERROR
from flask_babel import _

auth = Blueprint("auth", __name__, url_prefix="/auth")

@auth.before_request
def check_login_state():
    if session.get(SESSION_USER_TOKEN, None) is not None:
        return redirect(url_for("account.home"))
    return None  # proceed as normal

@auth.route("/login", methods=["GET", "POST"])
def login():
    username = ""
    if request.method == "POST":
        username = request.form.get(FORM_USERNAME)
        password = request.form.get(FORM_PASSWORD)
        assert_non_null_values(username, password)
        result = login_user(username, password)
        if result.is_value:
            session[SESSION_USER_TOKEN] = result.value
            return redirect(url_for("account.home"))
        flash(_(result.error), category=FLASH_ERROR)

    return render_template("login.html", username=username)


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get(FORM_USERNAME)
        password = request.form.get(FORM_PASSWORD)
        confirm_password = request.form.get(FORM_CONFIRM_PASSWORD)
        assert_non_null_values(username, password, confirm_password)
        result = register_user(username, password, confirm_password)
        if result is None:
            return redirect(url_for("auth.login"))
        print(result)
        flash(_(result), category=FLASH_ERROR)

    return render_template("register.html")


@auth.route("/logout")
def logout_web():
    token = session.get(SESSION_USER_TOKEN)
    if token is not None:
        logout(token)
    return redirect(url_for("auth.login"))