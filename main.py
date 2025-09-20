from flask import Flask, render_template, url_for, redirect, request, jsonify, session, send_file
from models import db, users, token, newdata, category
import os
from api import app as api_app
from login import change_password, change_username, check_username, checkuser, delete_account, loginChecker, validTokenChecker, logoutUser, checkRegistration, hash_pw
import secrets
from constants import USERID, TOKEN
from time import time
from sqlalchemy import func, distinct

with open(".env", "r") as f:
    for line in f.readlines():
        if line.strip() and not line.strip().startswith("#"):
            attr, val = line.lstrip().split("=", 1)
            os.environ[attr] = val.rstrip("\n")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://{}.lwanriaqqzgqslcendim:{}@{}:{}/{}".format(
    os.environ.get("uname"),
    os.environ.get("password"),
    os.environ.get("host"),
    os.environ.get("port"),
    os.environ.get("scheme")
)
app.config.update(
    BUNDLE_ERRORS = True,
    SECRET_KEY = os.urandom(40),
    SESSION_COOKIE_SECURE = False,
    SESSION_COOKIE_SAMESITE = "Strict"
)
#print(app.config["SQLALCHEMY_DATABASE_URI"])

app.register_blueprint(api_app)

db.init_app(app)

@app.route('/')
def index():
    return redirect("/login")

@app.route('/login',methods=["GET","POST"])
@loginChecker
def login():
    if request.method == "POST":
        username = request.form.get("username_input")
        password = request.form.get("password_input")
        if username is not None and password is not None and checkuser(username, password):
            # successful logged in
            # token cleanup
            for everySession in db.session.query(token).filter(token.expireTime < time()):
                db.session.delete(everySession)
            session[USERID] = db.session.query(users).filter(users.username==username).first().id #save in session[] currentUserId
            newToken = token(userid=session[USERID], token=secrets.token_urlsafe(96)) # 96 always produces a 128-long string, but idk why
            session[TOKEN] = newToken.token
            db.session.add(newToken)
            db.session.commit()
            return redirect("/home")
    return render_template('login.html')

@app.route('/register',methods=["GET","POST"])
def register():
    if request.method == "POST":
        username_input = request.form.get("username_input")
        password_1 = request.form.get("password_input_1")
        password_2 = request.form.get("password_input_2")
        if username_input is not None and password_1 is not None and password_2 is not None and checkRegistration(username_input, password_1, password_2) and check_username(username_input):
            # successful logged in
            # token cleanup
            
            newUserId = db.session.query(func.max(users.id)).scalar() + 1
            newUser = users(id=newUserId, username=username_input, password=hash_pw(password_1))
            db.session.add(newUser)
            db.session.commit()
            return redirect("/login")
    return render_template('register.html')

@app.route('/home')
@validTokenChecker
def home():
    return render_template('home.html', user_id=session.get(USERID), get_username=get_username)

@app.route('/edit')
@validTokenChecker
def edit():
    return render_template('edit.html', user_id=session.get(USERID), get_username=get_username)

@app.route('/profile', methods=["GET", "POST"])
@validTokenChecker
def profile():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "change-username":
            result = change_username(request.form.get("new_username"))

        elif action == "delete-account":
            result = delete_account(request.form.get("password"))
            if result is None:
                return redirect("/login")

        elif action == "change-password":
            current_pw = request.form.get("current-password")
            new_pw = request.form.get("new-password")
            new_pw_confirm = request.form.get("new-password-confirmation")
            result = change_password(current_pw, new_pw, new_pw_confirm)
            if result is None:
                return redirect("/login")
        
        else:
            result = "Unbekannte Aktion"
        print(f"{result=}")
    return render_template('profile.html', user_id=session.get(USERID), get_username=get_username)

@app.route("/logout")
def logout():
    token = session.get(TOKEN)
    logoutUser(token)

    return redirect("/login")

@app.route('/count', methods=['GET'])
@validTokenChecker
def count_entries():  # sourcery skip: use-named-expression
    user = db.session.query(users).filter(users.id == session.get(USERID)).first()
    if user:
        count = db.session.query(func.count(distinct(newdata.date))).filter(newdata.userid == user.id).scalar()
        #print(count)
        return jsonify(count=count)
    else:
        return jsonify(error="User not found"), 404
    

@app.route('/impressum')
def impressum():
    return render_template('impressum.html')

@app.route('/dpa')
def dpa():
    try:
        return send_file('static/docs/dpa.pdf', 
                         as_attachment=True)
    except Exception as e:
        return str(e)


def get_username() -> str:
    user = db.session.query(users).filter(users.id == session.get(USERID)).first()
    return user.username if user else ""


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8080, debug=os.environ.get("debug", False) == "True")
