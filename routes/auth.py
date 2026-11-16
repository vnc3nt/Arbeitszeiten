import secrets
from flask import Blueprint, render_template, redirect, request, session, url_for
from models import db, users, profiles, token
from constants import USERID, TOKEN, PROFILEID
from extensions import limiter
from login import loginChecker, checkuser, checkRegistration, check_username, hash_pw, hash_token, logoutUser, _get_valid_token
from time import time

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if _get_valid_token():
        return redirect("/home")
    return redirect("/login")


@auth_bp.route('/login', methods=["GET", "POST"])
@limiter.limit("10 per minute")
@loginChecker
def login():
    login_error = None
    if request.method == "POST":
        username = (request.form.get("username_input") or "").strip()
        password = request.form.get("password_input")
        if username and password and checkuser(username, password):
            db.session.query(token).filter(token.expiretime < int(time())).delete()
            user_obj = db.session.query(users).filter(users.username == username).first()
            session.clear()
            session.permanent = True
            session[USERID] = user_obj.id
            chosen_profile = None
            if user_obj.last_profile_id:
                chosen_profile = db.session.query(profiles).filter_by(
                    id=user_obj.last_profile_id, userid=user_obj.id, visible=True
                ).first()
            if not chosen_profile:
                chosen_profile = db.session.query(profiles).filter_by(
                    userid=user_obj.id, visible=True
                ).order_by(profiles.position.asc(), profiles.id.asc()).first()
            if not chosen_profile:
                chosen_profile = db.session.query(profiles).filter_by(userid=user_obj.id).order_by(profiles.id).first()

            if chosen_profile:
                session[PROFILEID] = chosen_profile.id
                user_obj.last_profile_id = chosen_profile.id

            raw_token = secrets.token_urlsafe(96)
            newToken = token(userid=session[USERID], token=hash_token(raw_token))
            session[TOKEN] = raw_token
            db.session.add(newToken)
            db.session.commit()
            return redirect("/home")
        login_error = "Benutzername oder Passwort ist falsch"
    return render_template('login.html', login_error=login_error)


@auth_bp.route('/register', methods=["GET", "POST"])
@limiter.limit("5 per minute")
def register():
    if request.method == "POST":
        username_input = (request.form.get("username_input") or "").strip()
        password_1 = request.form.get("password_input_1")
        password_2 = request.form.get("password_input_2")
        terms_checkbox = request.form.get("terms_checkbox")

        if not terms_checkbox:
            return render_template('register.html', error="Sie müssen den Datenschutzbestimmungen zustimmen.")

        if username_input and password_1 and password_2 and checkRegistration(username_input, password_1, password_2) and check_username(username_input):
            try:
                newUser = users(username=username_input, password=hash_pw(password_1))
                db.session.add(newUser)
                db.session.flush()

                db.session.add(profiles(
                    userid=newUser.id,
                    name="Standardprofil",
                    maxhours=0,
                    visible=True,
                ))
                db.session.commit()
                return redirect("/login")
            except Exception:
                db.session.rollback()
                return render_template('register.html', error="Benutzername existiert bereits.")
    return render_template('register.html')


@auth_bp.route("/logout", methods=["POST"])
def logout():
    current_token = session.get(TOKEN)
    logoutUser(current_token)
    return redirect("/login")
