import os
import hashlib
from typing import Optional
from functools import wraps
from time import time
from flask import session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from models import category, db, data, users, profiles, token, update_expire_time
from constants import USERID, TOKEN, PROFILEID, USERNAME_REGEX


def hash_pw(password: str) -> str:
    """Erstellt einen sicheren Passwort-Hash mit Salt (scrypt/pbkdf2)."""
    return generate_password_hash(password)


def checkuser(username: str, password: str) -> bool:
    user = db.session.query(users).filter(users.username == username).first()
    if user is None or not user.password:
        return False

    # 1. Prüfe modernes Werkzeug-Hash-Format (scrypt / pbkdf2)
    if user.password.startswith(("scrypt:", "pbkdf2:")):
        return check_password_hash(user.password, password)

    # 2. Fallback für alte SHA-512 Hashes + automatisches Upgrade beim Login!
    legacy_sha512 = hashlib.sha512(password.encode("utf-8")).hexdigest()
    if secrets_compare(user.password, legacy_sha512):
        user.password = hash_pw(password)
        db.session.commit()
        return True

    return False


def secrets_compare(val1: str, val2: str) -> bool:
    """Timing-Attack-sicherer String-Vergleich."""
    import hmac
    return hmac.compare_digest(val1, val2)


def check_username(username: str) -> bool:
    return USERNAME_REGEX.fullmatch(username) is not None


def delete_account(pw: Optional[str]):
    if not pw:
        return "Blank password"
    u = db.session.query(users).filter(users.id == session.get(USERID)).first()
    if not u:
        return "Benutzer nicht gefunden"

    if checkuser(u.username, pw):
        delete_user_data(u.id)
        session.clear()
        return None
    return "Falsches Passwort"


def delete_user_data(id: int):
    user = db.session.query(users).filter(users.id == id).first()
    if user and user.profile_image:
        image_path = os.path.join(os.path.dirname(__file__), "static", user.profile_image)
        if os.path.exists(image_path):
            os.remove(image_path)

    data.query.filter_by(userid=id).delete()
    token.query.filter_by(userid=id).delete()
    category.query.filter_by(userid=id).delete()
    profiles.query.filter_by(userid=id).delete()
    users.query.filter_by(id=id).delete()
    db.session.commit()


def change_username(new_username: Optional[str]):
    if not new_username:
        return "Blank/no username"

    new_username = new_username.strip()
    if not check_username(new_username):
        return "Benutzername darf keine Leerzeichen enthalten und muss mind. 8 Zeichen lang sein"

    # Explizite Prüfung, ob der Benutzername schon vergeben ist
    existing = db.session.query(users).filter(
        users.username == new_username,
        users.id != session.get(USERID)
    ).first()
    if existing:
        return "Username already exists"

    u = db.session.query(users).filter(users.id == session.get(USERID)).first()
    if not u:
        return "Benutzer nicht gefunden"

    u.username = new_username
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return "Username already exists"
    return None


def change_password(cur_pw, new_pw, new_pw_confirm):
    if not cur_pw or not new_pw or not new_pw_confirm:
        return "Blank password"

    u = db.session.query(users).filter(users.id == session.get(USERID)).first()
    if not u or not checkuser(u.username, cur_pw):
        return "Falsches Passwort"

    if new_pw != new_pw_confirm:
        return "Neues Passwort und Bestätigung sind verschieden"

    if len(new_pw) < 8:
        return "Passwort muss mindestens 8 Zeichen lang sein"

    u.password = hash_pw(new_pw)
    db.session.commit()
    logoutUser(session.get(TOKEN))
    return None


def checkRegistration(username: str, password_1: str, password_2: str) -> bool:
    user = db.session.query(users).filter(users.username == username).first()
    if user is None and password_1 == password_2 and len(password_1) >= 8:
        return True
    return False


def _get_valid_token():
    """Prüft, ob User-ID und Session-Token existieren, zusammenpassen und nicht abgelaufen sind."""
    user_id = session.get(USERID)
    session_token = session.get(TOKEN)
    if not user_id or not session_token:
        return None

    return db.session.query(token).filter(
        token.userid == user_id,
        token.token == session_token,
        token.expiretime > int(time())
    ).first()


def loginChecker(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        existingToken = _get_valid_token()
        if existingToken:
            existingToken.expiretime = update_expire_time()
            db.session.commit()
            return redirect("/home")
        return func(*args, **kwargs)
    return wrapper


def validTokenChecker(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        existingToken = _get_valid_token()
        if existingToken:
            existingToken.expiretime = update_expire_time()
            db.session.commit()
            return func(*args, **kwargs)
        session.clear()
        return redirect("/login")
    return wrapper


def logoutUser(currentToken):
    # Abgelaufene Tokens direkt per Bulk-Delete bereinigen
    db.session.query(token).filter(token.expiretime < int(time())).delete()

    if currentToken:
        delToken = db.session.query(token).filter(token.token == currentToken).first()
        if delToken:
            db.session.delete(delToken)

    db.session.commit()
    session.pop(TOKEN, None)
    session.pop(USERID, None)
    session.pop(PROFILEID, None)
    return redirect("/login")
