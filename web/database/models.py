from datetime import datetime, timedelta, timezone
from enum import Enum, auto
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, ForeignKey, MetaData, UniqueConstraint, func, text, BigInteger
from sqlalchemy.dialects import sqlite
from time import time

from shared.constants import API_DATE_FORMAT, API_DATETIME_FORMAT, CONSTRAINT_UNIQUE_PROFILE_CATEGORY, CONSTRAINT_UNIQUE_PROFILE_NAME, CONSTRAINT_UNIQUE_PROFILE_WORK_PERIOD
from shared.messages import msgid
from config.flask_settings import SQLALCHEMY_NAMING_CONVENTION


EXPIRE_TIME = 3600*24*7 #eine woche hält das token

db = SQLAlchemy(metadata=MetaData(naming_convention=SQLALCHEMY_NAMING_CONVENTION))

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
    MONTH = msgid("month")
    WEEK = msgid("week")
    
    def to_json(self):
        return self.name


class Users(db.Model):
    __tablename__ = "Users"
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, nullable=False, autoincrement=True)
    username = db.Column(db.String(30), nullable=False, unique=True, index=True)
    password = db.Column(db.String(128), nullable=False)
    salt = db.Column(db.String(32), nullable=False)
    picture_path = db.Column(db.String(10), nullable=True, server_default=text("NULL"))
    setting = db.Column(db.JSON, nullable=False, server_default=text("'{}'"))

class Profile(db.Model):  # TODO missing: (changable) order
    __tablename__ = "Profile"
    __table_args__ = (
        UniqueConstraint("userId", "name", name=CONSTRAINT_UNIQUE_PROFILE_NAME),  # prevents duplicate name on database
    )

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, nullable=False, autoincrement=True)
    userId = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), ForeignKey("Users.id", ondelete="cascade"), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    color = db.Column(db.String(6), nullable=True, server_default=text("NULL"))
    workStart = db.Column(db.Date, nullable=False)  # TODO: dates are weird because of timezones
    lastViewed = db.Column(db.TIMESTAMP, nullable=False)

    def to_json(self, *, include_entries: bool = False, include_work_periods: bool = False):
        data = {
                "id": self.id,
                "userId": self.userId,
                "name": self.name,
                "color": self.color,
                "workStart": self.workStart.strftime(API_DATE_FORMAT),
                "lastViewed": self.lastViewed.strftime(API_DATETIME_FORMAT)
        }
        if include_work_periods:
            work_periods = WorkTime.query.filter(WorkTime.profileId == self.id).order_by(WorkTime.workStart).all()
            data["work_periods"] = [x.to_json() for x in work_periods]

        if include_entries:
            entries = WorkTimeEntry.query.filter(WorkTimeEntry.profileCategoryId).order_by(WorkTimeEntry.workStart).all()
            data["entries"] = [x.to_json() for x in entries]
        return data

class WorkTime(db.Model):
    __tablename__ = "WorkTime"
    __table_args__ = (
        UniqueConstraint("profileId", "workStart", name=CONSTRAINT_UNIQUE_PROFILE_WORK_PERIOD),  # prevents duplicate name on database
    )
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, nullable=False, autoincrement=True)
    profileId = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), ForeignKey("Profile.id", ondelete="cascade"), nullable=False)
    profileCategoryId = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), ForeignKey("ProfileCategory.id", ondelete="cascade"), nullable=True)
    workTime = db.Column(db.Integer, CheckConstraint("workTime >= 0", name="positiveWorktime"),  nullable=False)
    workTimeFormat = db.Column(db.Enum(WorkTimeFormat), nullable=False)
    workStart = db.Column(db.Date, nullable=False)

    def to_json(self):
        return {
                "id": self.id,
                "profileId": self.profileId,
                "profileCategoryId": self.profileCategoryId,
                "workTime": self.workTime,
                "workTimeFormat": self.workTimeFormat.to_json(),
                "workStart": self.workStart.strftime(API_DATE_FORMAT)
        }


class ProfileCategory(db.Model):
    __tablename__ = "ProfileCategory"
    __table_args__ = (
        UniqueConstraint("profileId", "name", name=CONSTRAINT_UNIQUE_PROFILE_CATEGORY),  # prevents duplicate name on database
    )
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, nullable=False, autoincrement=True)
    profileId = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), ForeignKey("Profile.id", ondelete="cascade"), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    color = db.Column(db.String(6), nullable=False)

    def to_json(self, *, include_profile_id: bool = True):
        data = {
                "id": self.id,
                "name": self.name,
                "color": self.color
        }
        if include_profile_id:
            data["profileId"] = self.profileId
        return data

class WorkTimeEntry(db.Model):
    __tablename__ = "WorkTimeEntry"
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, nullable=False, autoincrement=True)
    profileCategoryId = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), ForeignKey("ProfileCategory.id", ondelete="restrict"), nullable=False)
    duration = db.Column(db.Integer, CheckConstraint("duration > 0", name="positiveDuration"), nullable=False)
    workStart = db.Column(db.TIMESTAMP(), nullable=False)
    entryTime = db.Column(db.TIMESTAMP, nullable=False, server_default=func.now())
    note = db.Column(db.Text, nullable=False, server_default="")

    def to_json(self, *, expandCategory: bool = True):
        data = {
                "id": self.id,
                "duration": self.duration,
                "workStart": self.workStart.strftime(API_DATE_FORMAT),
                "entryTime": self.entryTime.strftime(API_DATE_FORMAT),
                "note": self.note
        }
        if expandCategory:
            data["category"] = ProfileCategory.query.filter(ProfileCategory.id == self.profileCategoryId).first().to_json()
        else:
            data["categoryId"] = self.profileCategoryId
        return data



class Token(db.Model):
    __tablename__ = "Token"
    userId = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), ForeignKey("Users.id", ondelete="cascade"), nullable=False)
    token = db.Column(db.String(128), nullable=False, primary_key=True)
    expiretime = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), nullable=False, default=update_expire_time)
    tokenType = db.Column(db.Enum(TokenType), nullable=True)


# TODO: check necessity of index usage
