from flask import Blueprint, request, session

from blueprints.forms.profile import profile_forms
from blueprints.forms.work_time import work_time_forms
from shared.constants import SESSION_FORM_DATA
from shared.login import redirect_to_login_when_logged_out

forms = Blueprint("form", __name__, url_prefix="/form")
forms.before_request(redirect_to_login_when_logged_out)


@forms.before_request
def before_request():
    session[SESSION_FORM_DATA] = dict(request.form)


@forms.errorhandler(404)
def error404(error):
    return "Please use our website without programs"


@forms.errorhandler(400)
def error400(error):
    return "Please use our API instead"


forms.register_blueprint(profile_forms)
forms.register_blueprint(work_time_forms)
