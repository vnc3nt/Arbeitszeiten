from datetime import datetime, timedelta, timezone, date
from typing import Dict, Iterable, List, Optional, Tuple, Union

from sqlalchemy import and_, desc, not_, or_, text, func

from database import WorkTimeFormat
from database.models import Profile, ProfileCategory, WorkTimeEntry, db, WorkTime
from shared.messages import MESSAGE_CATEGORY_NOT_FOUND, MESSAGE_NO_WORK_TIME_FOUND, MESSAGE_NO_WORK_DONE
from shared.constants import API_DATETIME_FORMAT, API_DATE_FORMAT
from shared.util import Result, flatten, get_period_start, diff_month


def add_new_work(user_id: int, category_id: int, work_start: datetime, work_duration: timedelta, note: str) -> Result[WorkTimeEntry, Union[str, Dict]]:
    if work_duration < timedelta():
        return Result(error=MESSAGE_NO_WORK_DONE)
    work_end = work_start + work_duration
    category = ProfileCategory.query.join(Profile).filter(Profile.userId == user_id, ProfileCategory.id == category_id).first()
    if category is None:
        return Result(error=MESSAGE_CATEGORY_NOT_FOUND)
    overlap = work_overlaps(user_id, work_start, work_end)
    print(f"{overlap=}")
    if overlap is not None:
        return Result(error={"overlaps": overlap.to_json()})
    new_work_time = WorkTimeEntry(
            profileCategoryId = category_id,
            duration = int(work_duration.total_seconds()),
            workStart = work_start,
            entryTime = datetime.now(timezone.utc),
            note = note
    )
    db.session.add(new_work_time)
    db.session.commit()
    return Result(value=new_work_time)


def work_overlaps(user_id: int, work_start: datetime, work_end: datetime) -> Optional[WorkTimeEntry]:
    entries = list(filter_work_times(user_id, None, None, None, (work_start, work_end)))
    return entries[0] if entries else None


def filter_work_times(user_id: int, profile_id: Optional[int] = None, work_time_id: Optional[int] = None, category_id: Optional[int] = None, time_range: Optional[Tuple[datetime, datetime]] = None) -> Iterable[WorkTimeEntry]:
    query = WorkTimeEntry.query.select_from(WorkTimeEntry).join(ProfileCategory).join(Profile)
    query = query.filter(Profile.userId == user_id)
    if work_time_id:
        query = query.filter(WorkTimeEntry.id == work_time_id)

    if profile_id:
        query = query.filter(Profile.id == profile_id)

    if category_id:
        query = query.filter(ProfileCategory.id == category_id)

    entries = query.order_by(desc(WorkTimeEntry.workStart)).all()
    if time_range:
        result = []
        for entry in entries:
            entry_work_start = entry.workStart.replace(tzinfo=timezone.utc)
            entry_work_end = entry_work_start + timedelta(seconds=entry.duration)
            if entry_work_start < time_range[1] and entry_work_end > time_range[0]:
                result.append(entry)
        entries = result
    return entries


def delete_work_time(user_id, id: int) -> Result[WorkTimeEntry, str]:
    entry = WorkTimeEntry.query.select_from(WorkTimeEntry).join(ProfileCategory).join(Profile).filter(Profile.userId == user_id, WorkTimeEntry.id == id).first()
    if entry is None:
        return Result(error=MESSAGE_NO_WORK_TIME_FOUND)
    return Result(value=entry)


def delete_work_time_by_category(user_id: int, category_id: int) -> Result[List[WorkTimeEntry], str]:
    if category_id not in flatten(db.session.query(ProfileCategory.id).join(Profile).filter(Profile.userId == user_id)):
        return Result(error=MESSAGE_CATEGORY_NOT_FOUND)
    entries = WorkTimeEntry.query.select_from(WorkTimeEntry).join(ProfileCategory).join(Profile).filter(Profile.userId == user_id, ProfileCategory.id == category_id).all()
    for entry in entries:
        db.session.delete(entry)
    return Result(value=entries)

def get_period_balance(profile_id: int, begin: Union[datetime, date], end: Union[date, datetime]):
    if isinstance(begin, date):
        begin = datetime(year=begin.year, month=begin.month, day=begin.day)
    if isinstance(end, date):
        end = datetime(year=end.year, month=end.month, day=end.day)

    subquery = db.session.query(ProfileCategory.id).filter(ProfileCategory.profileId == profile_id).subquery()
    value = db.session.query(func.sum(WorkTimeEntry.duration)).filter(WorkTimeEntry.workStart >= begin, WorkTimeEntry.workStart < end, WorkTimeEntry.profileCategoryId.in_(subquery)).all()

    if value[0][0] is None:
        return 0.0
    return value[0][0] / 3600.0  # seconds to hours


def get_total_balance(profile_id: int, tzMinOffset: int = 0):
    balance = 0
    work_times: List[WorkTime] = WorkTime.query.filter(WorkTime.profileId == profile_id).order_by(desc(WorkTime.workStart)).all()
    current_time = datetime.now(timezone.utc) + timedelta(minutes=tzMinOffset)
    while work_times:
        begin = work_times[0].workStart
        end = work_times[1].workStart if len(work_times) >= 2 else current_time

        if work_times[0].workTimeFormat == WorkTimeFormat.MONTH:
            amount = diff_month(begin, end) + 1
            balance -= amount * work_times[0].workTime

        elif work_times[0].workTimeFormat == WorkTimeFormat.WEEK:
            amount = (end - begin) / timedelta(days=7)
            balance -= amount * work_times[0].workTime

        work_time = db.session.query(func.sum(WorkTimeEntry.duration)).filter(WorkTimeEntry.workStart >= begin, WorkTimeEntry.workStart <= end).first()
        if work_time[0] is None:
            work_time = 0
        else:
            work_time = work_time[0] / 3600.0

        balance += work_time
        work_times = work_times[1:]

    return balance
