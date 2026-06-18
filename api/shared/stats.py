from datetime import datetime
from shared.util import get_period_start
from shared.work_time import filter_work_times


def total_work_time(user_id: int, profile_id: int, period: datetime):
    start = get_period_start(period)
    filter_work_times(user_id, profile_id=profile_id)
    