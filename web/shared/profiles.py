from datetime import datetime, timezone, date
from typing import Iterable, List, Optional, Union

from sqlalchemy import desc, asc

from database.models import ProfileCategory, WorkTime, WorkTimeFormat, db, Profile
from shared.util import Result, flatten, get_period_start
from shared.messages import MESSAGE_CATEGORY_NAME_ALREADY_USED, MESSAGE_CATEGORY_NOT_FOUND, MESSAGE_CATEGORY_ONE_NEEDED, MESSAGE_NOT_ENOUGH_FILTERS_GIVEN, MESSAGE_PROFILE_NAME_USED, MESSAGE_PROFILE_NOT_FOUND
from shared.constants import DEFAULT_CATEGORIES


def create_profile(user_id: int, name: str, color: str, work_start: datetime, work_period: WorkTimeFormat, work_time: int) -> Result[Profile, str]:
    if name in get_user_profile_names(user_id):
        return Result(error=MESSAGE_PROFILE_NAME_USED)

    profile = Profile(
            userId = user_id,
            name=name,
            color=color,
            workStart=work_start.date(),
            lastViewed=datetime.now(timezone.utc)
    )
    db.session.add(profile)
    db.session.flush()

    # this function will commit adding the profile and can't fail because new profile
    set_work_period(profile.id, work_time, get_period_start(work_start, work_period), work_period, None)

    for category_name, color in DEFAULT_CATEGORIES:
        create_category(user_id, profile.id, category_name, color)  # should not fail because it is a new profile

    return Result(value=profile)


def get_user_profile_names(user_id) -> Iterable[str]:
    return flatten(db.session.query(Profile.name).filter(Profile.userId == user_id).all())

def get_user_profile_ids(user_id) -> Iterable[int]:
    return flatten(db.session.query(Profile.id).filter(Profile.userId == user_id).all())

def get_user_profiles(user_id) -> List[Profile]:
    return Profile.query.filter(Profile.userId == user_id).all()

def get_work_period(profile_id: int, time: Union[date, datetime]) -> WorkTime:
    work_time = WorkTime.query.filter(WorkTime.profileId == profile_id, WorkTime.workStart <= time).order_by(desc(WorkTime.workStart)).first()
    if work_time is None:
        return WorkTime.query.filter(WorkTime.profileId == profile_id).order_by(asc(WorkTime.workStart)).first()
    return work_time

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

    if name is not None:
        if name in get_user_profile_names(user_id):
            return Result(error=MESSAGE_PROFILE_NAME_USED)
        profile.name = name

    if color is not None:
        profile.color = color

    db.session.commit()
    return Result(value=profile)


def delete_profile(user_id: int, profile_id: int) -> bool:
    success = Profile.query.filter(Profile.userId == user_id, Profile.id == profile_id).delete() >= 1
    print(success)
    db.session.commit()
    return success


def create_category(user_id: int, profile_id: int, name: str, color: str):
    if profile_id not in get_user_profile_ids(user_id):
        return Result(error=MESSAGE_PROFILE_NOT_FOUND)
    if name in get_category_names(profile_id):
        return Result(error=MESSAGE_CATEGORY_NAME_ALREADY_USED)
    category = ProfileCategory(
        profileId=profile_id,
        name=name,
        color=color
    )
    db.session.add(category)
    db.session.commit()
    return Result(value=category)


def get_category_names(profile_id: int) -> Iterable[str]:
    """Assumes correct profile id"""
    return flatten(db.session.query(ProfileCategory.name).filter(ProfileCategory.profileId == profile_id).order_by(ProfileCategory.id).all())

def get_profile_categories(user_id: int, profile_id: int) -> Result[List[ProfileCategory], str]:
    if profile_id not in get_user_profile_ids(user_id):
        return Result(error=MESSAGE_PROFILE_NOT_FOUND)

    return Result(value=ProfileCategory.query.filter(ProfileCategory.profileId).all())


def get_categories(user_id: int, profile_id: Optional[int] = None, category_id: Optional[int] = None) -> Result[List[ProfileCategory], str]:
    if profile_id is None and category_id is None:
        return Result(error=MESSAGE_NOT_ENOUGH_FILTERS_GIVEN)

    query = ProfileCategory.query
    if profile_id is not None:
        if profile_id not in get_user_profile_ids(user_id):
            return Result(error=MESSAGE_PROFILE_NOT_FOUND)
        query = query.filter(ProfileCategory.profileId == profile_id)

    if category_id is not None:
        query = query.filter(ProfileCategory.id == category_id)

    categories = query.all()

    if profile_id is None and category_id is not None and categories[0].profileId not in get_user_profile_ids(user_id):
        return Result(error=MESSAGE_CATEGORY_NAME_ALREADY_USED)

    return Result(value=categories)


def delete_category(user_id: int, category_id: int) -> Result[ProfileCategory, str]:
    category = db.session.query(ProfileCategory).join(Profile).filter(Profile.userId == user_id, ProfileCategory.id == category_id).first()
    if category is None:
        return Result(error=MESSAGE_CATEGORY_NOT_FOUND)
    if len(list(get_category_names(category.profileId))) == 1:
        return Result(error=MESSAGE_CATEGORY_ONE_NEEDED)
    db.session.delete(category)
    db.session.commit()
    return Result(value=category)


def update_category(user_id: int, category_id: int, *, name: Optional[str] = None, color: Optional[str] = None) -> Result[ProfileCategory, str]:
    category = ProfileCategory.query.join(Profile).filter(Profile.id == user_id, ProfileCategory.id == category_id).first()
    if category is None:
        return Result(error=MESSAGE_CATEGORY_NOT_FOUND)

    if name is not None:
        if name in get_category_names(category.profileId):
            return Result(error=MESSAGE_CATEGORY_NAME_ALREADY_USED)
        category.name = name
    if color is not None:
        category.color = color

    return Result(value=category)

