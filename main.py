import os
from datetime import timedelta
from urllib.parse import quote

from dotenv import load_dotenv
from flask import Flask, request, session
from werkzeug.middleware.proxy_fix import ProxyFix

from api import app as api_app
from db_setup import ensure_profile_image_column, ensure_profiles
from extensions import csrf, limiter
from models import EXPIRE_TIME, db
from routes.auth import auth_bp
from routes.home import home_bp
from routes.legal import legal_bp
from routes.profile import profile_bp
from translations import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    get_translation,
)
from utils.formatting import decimal_comma_filter
from utils.session_helpers import (
    SUPPORTED_THEMES,
    get_current_language,
    get_current_theme,
)

load_dotenv()


def _database_url():
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return database_url

    values = {
        "uname": os.environ.get("uname"),
        "db": os.environ.get("db"),
        "password": os.environ.get("password"),
        "host": os.environ.get("host"),
    }
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise RuntimeError(
            "Fehlende Supabase-Konfiguration in .env: "
            + ", ".join(missing)
            + ". Alternativ DATABASE_URL setzen."
        )
    port = os.environ.get("port", "6543")
    scheme = os.environ.get("scheme", "postgres")
    return (
        f"postgresql://{quote(values['uname'], safe='')}.{quote(values['db'], safe='')}:"
        f"{quote(values['password'], safe='')}@{values['host']}:{port}/{scheme}"
    )


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config["SQLALCHEMY_DATABASE_URI"] = _database_url()
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "connect_args": {"options": "-csearch_path=arbeitszeiten,public"},
}

secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    raise RuntimeError("KRITISCH: SECRET_KEY Umgebungsvariable ist nicht gesetzt!")

app.config.update(
    BUNDLE_ERRORS=True,
    SECRET_KEY=secret_key,
    PERMANENT_SESSION_LIFETIME=timedelta(seconds=EXPIRE_TIME),
    SESSION_COOKIE_SECURE=os.environ.get("debug", "False") != "True",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    SEND_FILE_MAX_AGE_DEFAULT=31536000,
)

db.init_app(app)
csrf.init_app(app)
limiter.init_app(app)


@app.before_request
def make_session_permanent():
    session.permanent = True


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline';"
    )
    if request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response


@app.context_processor
def inject_translations():
    return {
        "current_lang": get_current_language(),
        "current_theme": get_current_theme(),
        "supported_languages": SUPPORTED_LANGUAGES,
        "supported_themes": SUPPORTED_THEMES,
        "t": lambda key, **kwargs: get_translation(
            key, get_current_language(), **kwargs
        ),
    }


app.template_filter("decimal_comma")(decimal_comma_filter)
app.register_blueprint(api_app)
app.register_blueprint(auth_bp)
app.register_blueprint(home_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(legal_bp)

# Keep the endpoint names used by existing templates and external links stable.
_endpoint_aliases = {
    "login": "auth.login",
    "register": "auth.register",
    "logout": "auth.logout",
    "home": "home.home",
    "switch_profile": "home.switch_profile",
    "manage_profile": "profile.manage_profile",
    "profile": "profile.profile",
    "export_data": "profile.export_data",
    "set_language": "profile.set_language",
    "set_theme": "profile.set_theme",
    "impressum": "legal.impressum",
    "dpa": "legal.dpa",
    "datenschutz": "legal.datenschutz",
    "agb": "legal.agb",
}
for alias, endpoint in _endpoint_aliases.items():
    view = app.view_functions[endpoint]
    app.add_url_rule(
        view.url_rule if hasattr(view, "url_rule") else app.url_map._rules_by_endpoint[endpoint][0].rule,
        endpoint=alias,
        view_func=view,
        methods=list(app.url_map._rules_by_endpoint[endpoint][0].methods),
    )

with app.app_context():
    db.create_all()
    ensure_profile_image_column()
    ensure_profiles()
    db.session.remove()
    db.engine.dispose()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("debug", False) == "True")
