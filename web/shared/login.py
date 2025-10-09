from time import time
from typing import Optional
from shared.messages import MESSAGE_INVALID_LOGIN_CREDENTIALS, MESSAGE_PASSWORD_DOES_NOT_MATCH, MESSAGE_USERNAME_ALREADY_TAKEN
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


def login_user(username: str, password: str) -> Result:
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
