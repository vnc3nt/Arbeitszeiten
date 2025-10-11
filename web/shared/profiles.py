from datetime import datetime, timezone, date
from typing import List, Optional

from sqlalchemy import desc

from database.models import WorkTime, WorkTimeFormat, db, Profile
from shared.util import Result, get_period_start
from shared.messages import MESSAGE_PROFILE_NAME_IN_USE, MESSAGE_PROFILE_NOT_FOUND

def create_profile(user_id: int, name: str, color: str, work_start: datetime, work_period: WorkTimeFormat, work_time: int) -> Result[Profile, str]:
    if name in get_user_profile_names(user_id):
        return Result(error=MESSAGE_PROFILE_NAME_IN_USE)

    profile = Profile(
            userId = user_id,
            name=name,
            color=color,
            workStart=work_start.date(),
            lastViewed=datetime.now(timezone.utc)
    )
    db.session.add(profile)
    db.session.flush()

    result = set_work_period(profile.id, work_time, get_period_start(work_start, work_period), work_period, None)  # this function will commit adding the profile

    # TODO create the default categories work and vacation
    return Result(value=profile)


def get_user_profile_names(user_id) -> List[str]:
    return db.session.query(Profile.name).filter(Profile.userId == user_id).all()

def get_user_profile_ids(user_id) -> List[int]:
    return db.session.query(Profile.id).filter(Profile.userId == user_id).all()

def get_user_profiles(user_id) -> List[Profile]:
    return Profile.query.filter(Profile.userId == user_id).all()

def set_work_period(profile_id: int, work_time: int, period_start: date, work_period: WorkTimeFormat, category_id: Optional[int] = None) -> Result[WorkTime, str]:
    """
    It is expected that profile_id is valid and correct

    Currently this function seems to not be able to fail
    """
    entry = WorkTime.query.filter(WorkTime.profileId==profile_id, WorkTime.workStart==period_start, WorkTime.profileCategoryId==category_id).first()
    if entry is None:
        wt = WorkTime(
                profileId=profile_id,
                workStart=period_start,
                workTimeFormat=work_period,
                workTime=work_time,
                profileCategoryId=category_id
        )
        db.session.add(wt)
        db.session.commit()
        return Result(value=wt)
    else:
        entry.workTime=work_time
        entry.workTimeFormat=WorkTimeFormat
        db.session.commit()
        return Result(value=entry)


def get_all_user_profiles(user_id: int) -> List[Profile]:
    return Profile.query.filter(Profile.userId == user_id).all()

def get_last_viewed_user_profile(user_id: int) -> Optional[Profile]:
    return Profile.query.filter(Profile.userId == user_id).order_by(desc(Profile.lastViewed)).first()

def get_user_profile_by_id(user_id: int, profile_id: int, update_last: bool) -> Optional[Profile]:
    # include user and profile id to make sure the profile belongs to the given person
    profile = Profile.query.filter(Profile.userId == user_id, Profile.id == profile_id).first()
    if profile is not None and update_last:
        profile.lastViewed = datetime.now(timezone.utc)
        db.session.commit()
    return profile


def update_user_profile(user_id: int, profile_id: int, *, name: Optional[str] = None, color: Optional[str] = None) -> Result[Profile, str]:
    profile = Profile.query.filter(Profile.userId == user_id, Profile.id == profile_id).first()
    if profile is None:
        return Result(error=MESSAGE_PROFILE_NOT_FOUND)
    if name in get_user_profile_names(user_id):
        return Result(error=MESSAGE_PROFILE_NAME_IN_USE)
    
    if name is not None:
        profile.name = name

    if color is not None:
        profile.color = color

    db.session.commit()
    return Result(value=profile)


def delete_profile(user_id: int, profile_id: int) -> bool:
    success = Profile.query.filter(Profile.userId == user_id, Profile.id == profile_id).delete() >= 1
    db.session.commit()
    return success
