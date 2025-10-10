from datetime import datetime, timezone
from enum import Enum, auto
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint, func, text, BigInteger
from sqlalchemy.dialects import sqlite
from time import time


EXPIRE_TIME = 3600*24*7 #eine woche hält das token

db = SQLAlchemy()

def current_date():
    time = datetime.now(timezone.utc)
    return datetime(day=time.day, month=time.month, year=time.year)

def update_expire_time():
    return int(time()) + EXPIRE_TIME #in seconds


class TokenType(Enum):
    IOS = auto()
    API = auto()
    DESKTOP = auto()

class WorkTimeFormat(Enum):
    MONTH = "month"
    HOUR = "hour"


class Users(db.Model):
    __tablename__ = "Users"
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, nullable=False, autoincrement=True)
    username = db.Column(db.String(30), nullable=False, unique=True, index=True)
    password = db.Column(db.String(128), nullable=False)
    salt = db.Column(db.String(32), nullable=False)
    picture_path = db.Column(db.String(10), nullable=True, server_default=text("NULL"))
    setting = db.Column(db.JSON, nullable=False, server_default=text("'{}'"))

class Profile(db.Model):
    __tablename__ = "Profile"
    __table_args__ = (
        UniqueConstraint("userId", "name"),  # prevents duplicate name on database
    )

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, nullable=False, autoincrement=True)
    userId = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), ForeignKey("Users.id", ondelete="cascade"), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    color = db.Column(db.String(6), nullable=True, server_default=text("NULL"))
    workStart = db.Column(db.Date, nullable=False)  # TODO: dates are weird because of timezones
    lastViewed = db.Column(db.TIMESTAMP, nullable=False)

class WorkTime(db.Model):
    __tablename__ = "WorkTime"
    __table_args__ = (
        UniqueConstraint("profileId", "workStart"),  # prevents duplicate name on database
    )
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, nullable=False, autoincrement=True)
    profileId = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), ForeignKey("Profile.id", ondelete="cascade"), nullable=False)
    profileCategoryId = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), ForeignKey("ProfileCategory.id", ondelete="cascade"), nullable=True)
    workTime = db.Column(db.Integer, CheckConstraint("workTime >= 0"),  nullable=False)
    workTimeFormat = db.Column(db.Enum(WorkTimeFormat), nullable=False)
    workStart = db.Column(db.Date, nullable=False)


class ProfileCategory(db.Model):
    __tablename__ = "ProfileCategory"
    __table_args__ = (
        UniqueConstraint("profileId", "name"),  # prevents duplicate name on database
    )
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, nullable=False, autoincrement=True)
    profileId = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), ForeignKey("Profile.id", ondelete="cascade"), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    color = db.Column(db.String(6), nullable=False)

class WorkTimeEntry(db.Model):
    __tablename__ = "WorkTimeEntry"
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, nullable=False, autoincrement=True)
    profileCategoryId = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), ForeignKey("ProfileCategory.id", ondelete="cascade"), nullable=False)
    duration = db.Column(db.Integer, CheckConstraint("duration > 0"), nullable=False)
    workStart = db.Column(db.TIMESTAMP, nullable=False)
    entryTime = db.Column(db.TIMESTAMP, nullable=False, server_default=func.now())
    note = db.Column(db.Text, nullable=False, server_default="")


class Token(db.Model):
    __tablename__ = "Token"
    userId = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), ForeignKey("Users.id", ondelete="cascade"), nullable=False)
    token = db.Column(db.String(128), nullable=False, primary_key=True)
    expiretime = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), nullable=False, default=update_expire_time)
    tokenType = db.Column(db.Enum(TokenType), nullable=True)


# TODO: check necessity of index usage
