from typing import Optional
from models import category, db, newdata,users,token,update_expire_time
import hashlib
from flask import session, redirect
from constants import USERID, TOKEN, USERNAME_REGEX
from functools import wraps
from time import time

def checkuser(username:str, password:str) -> bool:
    user = db.session.query(users).filter(users.username == username).first()
    if user is None:
        return False
    userpw = user.password
    return userpw == hash_pw(password)

def check_username(username: str) -> bool:
    return USERNAME_REGEX.fullmatch(username) is None

def delete_account(pw: Optional[str]):
    if not pw:
        return "Blank password"
    u = db.session.query(users).filter(users.id == session.get(USERID)).first()
    valid_pw = checkuser(u.username, pw)
    if valid_pw:
        delete_user_data(u.id)
    else:
        return "Falsches Passwort"

def delete_user_data(id: int):
    newdata.query.filter_by(userid=id).delete()
    token.query.filter_by(userid=id).delete()
    category.query.filter_by(userId=id).delete()
    users.query.filter_by(id=id).delete()

    db.session.commit()


def change_username(new_username: Optional[str]):
    print(new_username)
    if not new_username:  # stops also empty string
        return "Blank/no username"

    if not check_username(new_username):
        return "Benutzername darf keine Leerzeichen enthalten"
    
    u = db.session.query(users).filter(users.id == session.get(USERID)).first()
    u.username = new_username
    print("Changed username")
    try:
        db.session.commit()
    except:
        return "Username already exists"
    return None  # no issues

def change_password(cur_pw, new_pw, new_pw_confirm):
    if not cur_pw or not new_pw or not new_pw_confirm:
        return "Blank password"
    
    u = db.session.query(users).filter(users.id == session.get(USERID)).first()
    valid_pw = checkuser(u.username, cur_pw)
    if not valid_pw:
        return "Falsches Passwort"
    
    elif new_pw != new_pw_confirm:
        return "Neues Passwort und Best&auml;tigung sind verschieden"
    
    elif len(new_pw) < 8:
        return "Passwort muss mindestens 8 Zeichen lang sein"

    u.password = hash_pw(new_pw)
    db.session.commit()
    logoutUser(session.get(TOKEN))


def checkRegistration(username:str, password_1:str, password_2:str) -> bool:
    user = db.session.query(users).filter(users.username == username).first()
    if user is None:
        if password_1 == password_2:
            
            if len(password_1) >= 8:
                
                return True
            else:
                print("less than 8 characters")
        else:
            print("two different passwords")
    else:
        print("noUsername")

    return False

def hash_pw(password:str) -> str:
    return hashlib.sha512(bytes(password, encoding = "utf-8")).hexdigest()

def loginChecker(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        existingToken = db.session.query(token).filter(token.userid == session.get(USERID)).first()
        if existingToken:
            existingToken.expireTime = update_expire_time()
            db.session.commit()
            return redirect("/home")
        else:
            return func(*args, **kwargs)
    return wrapper
        
def validTokenChecker(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        existingToken = db.session.query(token).filter(token.userid == session.get(USERID)).first()
        if existingToken:
            existingToken.expireTime = update_expire_time()
            db.session.commit()
            return func(*args, **kwargs)
        else:
            return redirect("/login")
    return wrapper


def logoutUser(currentToken):
    # token cleanup
    for everySession in db.session.query(token).filter(token.expireTime < time()):
        db.session.delete(everySession)

    if currentToken is None:
        db.session.commit()
        return

    delToken = db.session.query(token).filter(token.token==currentToken).first()
    print(delToken)
    print(currentToken)
    print(session)
    db.session.delete(delToken)
    db.session.commit()
    session.pop(TOKEN)
    session.pop(USERID)
    print(session)
    return redirect("/login")
