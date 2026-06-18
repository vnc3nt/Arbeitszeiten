from datetime import datetime, timezone

from flask import session, flash
from flask_babel import _

from shared.constants import SESSION_TIMER_INTERVALS, FLASH_SUCCESS, SESSION_TIMER_START
from web_util import convert_utc_to_local_time


def timer_get_first():
    return session[SESSION_TIMER_INTERVALS][0]

def timer_remove_first():
    session[SESSION_TIMER_INTERVALS] = session[SESSION_TIMER_INTERVALS][1:]
    if session[SESSION_TIMER_INTERVALS]:
        flash(_("work.timer.cleared"), FLASH_SUCCESS)
    return session[SESSION_TIMER_INTERVALS]

def timer_begin():
    session[SESSION_TIMER_START] = convert_utc_to_local_time(datetime.now(timezone.utc))
    if session.get(SESSION_TIMER_INTERVALS) is None:
        session[SESSION_TIMER_INTERVALS] = []

def timer_pause():
    session[SESSION_TIMER_INTERVALS].append(
        (session[SESSION_TIMER_START], convert_utc_to_local_time(datetime.now(timezone.utc)))
    )
    session[SESSION_TIMER_START] = None
    return session[SESSION_TIMER_INTERVALS]

def timer_has_entry():
    intervals = session.get(SESSION_TIMER_INTERVALS)
    return intervals is not None and len(intervals) >= 1
