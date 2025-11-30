from flask import Blueprint, render_template

auth = Blueprint("auth", __name__, url_prefix="/auth")

@auth.before_request
def check_login_state():
    if False and logged_in:
        return url_for("account.home")
    return None  # proceed as normal

@auth.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html")


@auth.route("/register", methods=["GET", "POST"])
def register():
    return render_template("register.html")