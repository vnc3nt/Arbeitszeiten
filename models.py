from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from time import time

EXPIRE_TIME = 3600*24*7 #eine woche hält das token

db = SQLAlchemy()
def current_date():
    time = datetime.now(timezone.utc)
    return datetime(day=time.day, month=time.month, year=time.year)
def update_expire_time():
    return int(time()) + EXPIRE_TIME #in seconds

class users(db.Model):
    id=db.Column(db.BIGINT, primary_key=True, nullable=False)
    username=db.Column(db.String(30), nullable=False)
    password=db.Column(db.String(128), nullable=False)

class newdata(db.Model):
    userid=db.Column(db.BIGINT, ForeignKey("users.id"), nullable=False, primary_key=True)
    date=db.Column(db.DATE, nullable=False, primary_key=True, default=current_date)
    categoryId=db.Column(db.BIGINT,ForeignKey("category.id"), nullable=False, primary_key=True)
    data=db.Column(db.Numeric(5,2), nullable=True)

class category(db.Model):
    id=db.Column(db.BIGINT, primary_key=True, nullable=False)
    userId=db.Column(db.BIGINT, ForeignKey("users.id"), nullable=False, primary_key=True)
    name=db.Column(db.String(30), nullable=False)
    color=db.Column(db.String(7), nullable=False)
    unit=db.Column(db.String(3), nullable=True)

class token(db.Model):
    userid=db.Column(db.BIGINT, ForeignKey("users.id"), nullable=False)
    token=db.Column(db.String(128), nullable=False, primary_key=True)
    expireTime=db.Column(db.BIGINT, nullable=False, default=update_expire_time)
