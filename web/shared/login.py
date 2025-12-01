from flask import g, redirect, url_for
from time import time
from typing import Optional

from sqlalchemy import or_
from shared.messages import MESSAGE_INVALID_LOGIN_CREDENTIALS, MESSAGE_PASSWORD_DOES_NOT_MATCH, MESSAGE_USERNAME_ALREADY_TAKEN
from shared.constants import G_USER, G_USER_TOKEN
from database.models import EXPIRE_TIME, Token, Users, db, TokenType
import hashlib
import secrets

from shared.util import Result



def hash_password(username: str, password: str, salt: str) -> str:
    return hashlib.sha256(bytes(password + username + salt, encoding="utf-8")).hexdigest()

def generate_salt():
    return secrets.token_urlsafe(24)  # has a length of 32 characters

def get_user_by_name(username: str) -> Optional[Users]:
    return Users.query.filter(Users.username == username).first()

def register_user(username: str, password: str, confirm_password: str) -> Optional[str]:
    if password != confirm_password:
        return MESSAGE_PASSWORD_DOES_NOT_MATCH
    if get_user_by_name(username) is not None:
        return MESSAGE_USERNAME_ALREADY_TAKEN

    salt = generate_salt()

    db.session.add(
            Users(
                username=username,
                password=hash_password(username, password, salt),
                salt=salt,
                picture_path=None
            )
    )
    db.session.commit()
    return None


def login_user(username: str, password: str) -> Result[str, str]:
    user = get_user_by_name(username)
    if user is None:
        return Result(error=MESSAGE_INVALID_LOGIN_CREDENTIALS)

    entered_password_hash = hash_password(username, password, user.salt)

    if entered_password_hash != user.password:
        return Result(error=MESSAGE_INVALID_LOGIN_CREDENTIALS)

    # password is correct and user exists
    token = create_user_token(user)
    db.session.add(token)
    db.session.commit()
    return Result(value=token.token)


def create_user_token(user: Users) -> Token:
    return Token(
        userId = user.id,
        token = secrets.token_urlsafe(96),  # length of 128 chars
        expiretime = time() + EXPIRE_TIME,
        tokenType = TokenType.API
    )

def logout(token: str) -> int:
    token_obj = Token.query.filter(Token.token == token).first()
    if token_obj is None:
        return 0
    deleted = Token.query.filter(or_(Token.token == token, Token.expiretime < time())).delete() > 0
    db.session.commit()
    return deleted


def is_valid_token(token: str, refresh: bool = True) -> bool:
    t = Token.query.filter(Token.token == token, Token.expiretime > time()).first()
    if t is None:
        return False
    if refresh:
        Token.query.filter(Token.token == token).update({"expiretime": time() + EXPIRE_TIME})
        db.session.commit()
    return True

def get_user(token: str) -> Users:
    return Users.query.join(Token).filter(Token.token == token).first()


def redirect_to_login_when_logged_out():
    token = getattr(g, G_USER_TOKEN, None)
    if token is None or not is_valid_token(token):
        return redirect(url_for("auth.login"))
    
    setattr(g, G_USER, get_user(token))