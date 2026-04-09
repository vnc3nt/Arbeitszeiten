from flask import Flask, g, redirect, url_for, request, session
from flask import Flask, g, redirect, url_for, request, session
from flask_babel import Babel

import shared.constants as __consts
from blueprints.account import account as account_app
from blueprints.api import app as api_app
from blueprints.auth import auth as auth_app
from blueprints.stats import stats as stats_app
from blueprints.forms import forms as form_handler
from database import db, WorkTimeFormat
from database.migrations import migrate
from shared.constants import G_USER, SESSION_FORM_DATA

app = Flask(__name__)
app.config.from_pyfile("config/flask_settings.py")
db.init_app(app)
migrate.init_app(app, db)


def get_locale():
    locale = request.accept_languages.best_match(app.config['BABEL_LANGUAGES'])
    return locale


babel = Babel(app, locale_selector=get_locale)
app.jinja_env.globals["get_locale"] = get_locale
app.jinja_env.globals["WORK_TIME_FORMATS"] = WorkTimeFormat
app.jinja_env.globals["gget"] = lambda key: session.get(SESSION_FORM_DATA, {}).get(key, "")

for variable in dir(__consts):
    app.jinja_env.globals[variable] = getattr(__consts, variable)


# called when request is canceled/finished
@app.teardown_appcontext
def teardown_appcontext(_):
    # clear g cache
    g.pop(G_USER, None)


app.register_blueprint(api_app)
app.register_blueprint(auth_app)
app.register_blueprint(account_app)
app.register_blueprint(form_handler)
app.register_blueprint(stats_app)


def main():
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8080)


@app.route("/")
def index():
    return redirect(url_for("auth.login"))


if __name__ == "__main__":
    main()
