from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Union

from sqlalchemy import and_, not_, or_

from database.models import Profile, ProfileCategory, WorkTimeEntry, db
from shared.messages import MESSAGE_CATEGORY_NOT_FOUND
from shared.util import Result


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
    return WorkTimeEntry.query \
        .select_from(WorkTimeEntry) \
        .join(ProfileCategory) \
        .join(Profile) \
        .filter(
                Profile.userId == user_id,
                (and_(
                    WorkTimeEntry.workStart < work_end,
                    WorkTimeEntry.duration + WorkTimeEntry.workStart > work_start
                ))
        ) \
        .first()

def filter_work_times(user_id: int, work_time_id: Optional[int], profile_id: Optional[int], category_id: Optional[int], time_range: Optional[Tuple[datetime, datetime]]) -> List[WorkTimeEntry]:
    query = WorkTimeEntry.query.select_from(WorkTimeEntry).join(ProfileCategory).join(Profile)
    query = query.filter(Profile.userId == user_id)
    if work_time_id:
        query = query.filter(WorkTimeEntry.id == work_time_id)

    if profile_id:
        query = query.filter(Profile.id == profile_id)

    if category_id:
        query = query.filter(ProfileCategory.id == category_id)

    if time_range:
        query = query.filter(
            and_(
                WorkTimeEntry.workStart < time_range[1],
                WorkTimeEntry.duration * timedelta(seconds=1) + WorkTimeEntry.workStart > time_range[0]
            )
        )

    return query.all()

