from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Tuple, Union

from sqlalchemy import and_, not_, or_

from database.models import Profile, ProfileCategory, WorkTimeEntry, db
from shared.messages import MESSAGE_CATEGORY_NOT_FOUND, MESSAGE_NO_WORK_TIME_FOUND
from shared.util import Result, flatten


def add_new_work(user_id: int, category_id: int, work_start: datetime, work_duration: timedelta, note: str) -> Result[WorkTimeEntry, Union[str, Dict]]:
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


def filter_work_times(user_id: int, work_time_id: Optional[int], profile_id: Optional[int], category_id: Optional[int], time_range: Optional[Tuple[datetime, datetime]]) -> Iterable[WorkTimeEntry]:
    query = WorkTimeEntry.query.select_from(WorkTimeEntry).join(ProfileCategory).join(Profile)
    query = query.filter(Profile.userId == user_id)
    if work_time_id:
        query = query.filter(WorkTimeEntry.id == work_time_id)

    if profile_id:
        query = query.filter(Profile.id == profile_id)

    if category_id:
        query = query.filter(ProfileCategory.id == category_id)

    if time_range:
        entries = query.all()
        for entry in entries:
            entry_workStart = entry.workStart.replace(tzinfo=timezone.utc)
            entry_workEnd = entry_workStart + timedelta(seconds=entry.duration)
            if entry_workStart < time_range[1] and entry_workEnd > time_range[0]:
                yield entry

    else:
        return query.all()


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
