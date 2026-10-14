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
    __table_args__ = {'schema': 'arbeitszeiten'}
    id = db.Column(db.BIGINT, primary_key=True, autoincrement=True, nullable=False)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Erweitert auf 255 für sichere Hashes
    profile_image = db.Column(db.Text, nullable=True)
    language = db.Column(db.String(10), nullable=False, default='de')
    theme = db.Column(db.String(10), nullable=False, default='auto')

class profiles(db.Model):
    __table_args__ = (
        db.UniqueConstraint("userid", "name", name="uq_profiles_user_name"),
        {"schema": "arbeitszeiten"},
    )
    id = db.Column(db.BIGINT, primary_key=True, autoincrement=True, nullable=False)
    userid = db.Column(db.BIGINT, ForeignKey("arbeitszeiten.users.id"), nullable=False)
    name = db.Column(db.String(30), nullable=False)
    maxhours = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    visible = db.Column(db.Boolean, nullable=False, default=True)
    position = db.Column(db.Integer, nullable=False, default=0)


class data(db.Model):
    __table_args__ = {'schema': 'arbeitszeiten'}
    userid=db.Column(db.BIGINT, ForeignKey("arbeitszeiten.users.id"), nullable=False, primary_key=True)
    date=db.Column(db.DATE, nullable=False, primary_key=True, default=current_date)
    categoryid=db.Column(db.BIGINT,ForeignKey("arbeitszeiten.category.id"), nullable=True, primary_key=False)
    profileid=db.Column(db.BIGINT, ForeignKey("arbeitszeiten.profiles.id"), nullable=False, primary_key=True)
    data=db.Column(db.Numeric(5,2), nullable=True)
    maxhours=db.Column(db.Numeric(5,2), nullable=True)

class category(db.Model):
    __table_args__ = {'schema': 'arbeitszeiten'}
    id = db.Column(db.BIGINT, primary_key=True, autoincrement=True, nullable=False)
    userid = db.Column(db.BIGINT, ForeignKey("arbeitszeiten.users.id"), nullable=False)
    name = db.Column(db.String(30), nullable=False)
    color = db.Column(db.String(7), nullable=False)
    profileid = db.Column(db.BIGINT, ForeignKey("arbeitszeiten.profiles.id"), nullable=False)

class token(db.Model):
    __table_args__ = {'schema': 'arbeitszeiten'}
    userid=db.Column(db.BIGINT, ForeignKey("arbeitszeiten.users.id"), nullable=False)
    token=db.Column(db.String(128), nullable=False, primary_key=True)
    expiretime=db.Column(db.BIGINT, nullable=False, default=update_expire_time)
