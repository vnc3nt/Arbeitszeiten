from flask import g, session, request
from models import db, users, profiles
from constants import USERID, PROFILEID
from translations import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE

SUPPORTED_THEMES = {'auto': 'Automatisch', 'dark': 'Darkmode', 'light': 'Lightmode'}


def get_current_language() -> str:
    if hasattr(g, "_current_language"):
        return g._current_language
    lang = session.get('lang')
    if lang in SUPPORTED_LANGUAGES:
        g._current_language = lang
        return lang
    user_id = session.get(USERID)
    if user_id:
        user = db.session.query(users).filter_by(id=user_id).first()
        if user and getattr(user, 'language', None) in SUPPORTED_LANGUAGES:
            session['lang'] = user.language
            g._current_language = user.language
            return user.language
    cookie_lang = request.cookies.get('lang')
    if cookie_lang in SUPPORTED_LANGUAGES:
        g._current_language = cookie_lang
        return cookie_lang
    g._current_language = DEFAULT_LANGUAGE
    return DEFAULT_LANGUAGE


def get_current_theme() -> str:
    if hasattr(g, "_current_theme"):
        return g._current_theme
    theme = session.get('theme')
    if theme in SUPPORTED_THEMES:
        g._current_theme = theme
        return theme
    user_id = session.get(USERID)
    if user_id:
        user = db.session.query(users).filter_by(id=user_id).first()
        if user and getattr(user, 'theme', None) in SUPPORTED_THEMES:
            session['theme'] = user.theme
            g._current_theme = user.theme
            return user.theme
    cookie_theme = request.cookies.get('theme')
    if cookie_theme in SUPPORTED_THEMES:
        g._current_theme = cookie_theme
        return cookie_theme
    g._current_theme = 'auto'
    return 'auto'


def get_active_profile():
    if hasattr(g, "_active_profile"):
        return g._active_profile
    profile_id = session.get(PROFILEID)
    account_id = session.get(USERID)
    if account_id is None:
        g._active_profile = None
        return None

    user = db.session.query(users).filter_by(id=account_id).first()

    # Wenn kein Profil in Session, versuche das in der DB gespeicherte zuletzt genutzte Profil
    if profile_id is None and user and user.last_profile_id:
        profile_id = user.last_profile_id

    profile = db.session.query(profiles).filter(
        profiles.id == profile_id,
        profiles.userid == account_id,
        profiles.visible.is_(True),
    ).first()

    if profile is None:
        profile = db.session.query(profiles).filter_by(
            userid=account_id, visible=True
        ).order_by(profiles.position.asc(), profiles.id.asc()).first()
        if profile is None:
            profile = db.session.query(profiles).filter_by(userid=account_id).order_by(profiles.id).first()

    if profile:
        session[PROFILEID] = profile.id
        if user and user.last_profile_id != profile.id:
            user.last_profile_id = profile.id
            db.session.commit()

    g._active_profile = profile
    return profile


def get_profile_list():
    if hasattr(g, "_profile_list"):
        return g._profile_list
    g._profile_list = db.session.query(profiles).filter_by(
        userid=session.get(USERID), visible=True
    ).order_by(profiles.position.asc(), profiles.id.asc()).all()
    return g._profile_list


def get_all_profile_list():
    if hasattr(g, "_all_profile_list"):
        return g._all_profile_list
    g._all_profile_list = db.session.query(profiles).filter_by(
        userid=session.get(USERID)
    ).order_by(profiles.position.asc(), profiles.id.asc()).all()
    return g._all_profile_list


def get_active_profile_name():
    profile = get_active_profile()
    return profile.name if profile else get_username()


def get_current_user():
    if not hasattr(g, "_current_user"):
        g._current_user = db.session.query(users).filter(users.id == session.get(USERID)).first()
    return g._current_user


def get_username() -> str:
    user = get_current_user()
    return user.username if user else ""
