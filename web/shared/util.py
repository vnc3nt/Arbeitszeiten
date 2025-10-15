import itertools
from datetime import datetime, date, timedelta
from typing import Any, Generic, Iterable, Optional, TypeVar, Union

from database.models import WorkTimeFormat

T = TypeVar("T")
E = TypeVar("E")

class Result(Generic[T, E]):
    def __init__(self, value: Optional[T] = None, error: Optional[E] = None):
        assert value is None or error is None, "Result can either be a value or an error, but not both"
        self.__data = value, error
        self.__error = error is not None

    def __repr__(self):
        if self.is_error:
            return f"Result(error={self.error})"
        else:
            return f"Result(value={self.value})"

    @property
    def value(self) -> T:
        assert self.is_value, "cannot retrieve value of an error Result"
        return self.__data[0]  # type: ignore

    @property
    def error(self) -> E:
        assert self.is_error, "cannot retrieve error of an value Result"
        return self.__data[1]  # type: ignore

    @property
    def is_value(self) -> bool:
        return not self.__error

    @property
    def is_error(self) -> bool:
        return self.__error




def get_period_start(intervall_date: Union[datetime, date], work_period: WorkTimeFormat) -> date:
    if work_period == WorkTimeFormat.MONTH:
        return date(intervall_date.year, intervall_date.month, 1)
    elif work_period == WorkTimeFormat.WEEK:
        week_start = intervall_date - timedelta(days=intervall_date.weekday())
        return week_start if isinstance(week_start, date) else week_start.date()
    raise NotImplementedError("unknown work period:", work_period)  # exists if we ever implement other work periods


def flatten(nested_iterable: Iterable[Iterable[T]]) -> Iterable[T]:
    return itertools.chain.from_iterable(nested_iterable)
