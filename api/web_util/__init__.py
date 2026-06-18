from typing import Optional, Tuple
from flask import g, session
from datetime import datetime, timedelta

from database.models import Profile
from shared.constants import G_CURRENT_PROFILE, SESSION_FORM_DATA, SESSION_TIMEZONE_OFFSET
from shared.profiles import get_last_viewed_user_profile, get_user_profile_by_id
from shared.util import Result


def get_current_profile(user_id: int) -> Optional[Profile]:
    profile_id = g.get(G_CURRENT_PROFILE)
    if profile_id is not None:
        return get_user_profile_by_id(user_id, profile_id, update_last=False)
    return get_last_viewed_user_profile(user_id)


def switch_profile(user_id: int, profile_id) -> Optional[Profile]:
    g.setdefault(G_CURRENT_PROFILE, profile_id)
    return get_user_profile_by_id(user_id, profile_id, update_last=True)

def clear_form_cache():
    session.pop(SESSION_FORM_DATA)

def convert_utc_to_local_time(time: datetime) -> datetime:
    return time + timedelta(minutes=-session.get(SESSION_TIMEZONE_OFFSET, 0))