import os
from flask import Blueprint, render_template, request, send_file, session, url_for
from translations import SUPPORTED_LANGUAGES
from utils.session_helpers import get_current_language
from login import _get_valid_token

legal_bp = Blueprint("legal", __name__)


@legal_bp.route("/impressum")
def impressum():
    is_authenticated = _get_valid_token() is not None
    fallback_endpoint = "home.home" if is_authenticated else "auth.login"
    fallback_url = url_for(fallback_endpoint)
    referrer = request.referrer
    if referrer and "/impressum" not in referrer:
        session["impressum_back_url"] = referrer
    elif not session.get("impressum_back_url"):
        session["impressum_back_url"] = fallback_url
    return render_template(
        "impressum.html",
        back_url=session.get("impressum_back_url") or fallback_url,
        is_authenticated=is_authenticated,
    )


def _document(filename_template):
    lang = request.args.get("lang") or get_current_language()
    if lang not in SUPPORTED_LANGUAGES:
        lang = "de"
    filename = filename_template.format(lang=lang)
    filepath = os.path.join("static", "docs", filename)
    if not os.path.exists(filepath):
        return "Dokument nicht gefunden", 404
    return send_file(filepath, as_attachment=True, download_name=filename)


@legal_bp.route("/dpa")
def dpa():
    return _document("dpa_{lang}.pdf")


@legal_bp.route("/datenschutz")
def datenschutz():
    return _document("dpa_{lang}.pdf")


@legal_bp.route("/agb")
def agb():
    return _document("agb_{lang}.pdf")
