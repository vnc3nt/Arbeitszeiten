from flask import abort
import itertools
from datetime import datetime, date, timedelta
from typing import Any, Generic, Iterable, Optional, TypeVar, Union, Tuple

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


def get_period_length(period_begin: date, work_period: WorkTimeFormat):
    if work_period == WorkTimeFormat.MONTH:
        return date(year=period_begin.year + period_begin.month // 12, month=period_begin.month % 12 + 1, day=1) - period_begin
    elif work_period == WorkTimeFormat.WEEK:
        return timedelta(days=1)
    raise NotImplementedError("unknown work period:", work_period)  # exists if we ever implement other work periods


def flatten(nested_iterable: Iterable[Iterable[T]]) -> Iterable[T]:
    return itertools.chain.from_iterable(nested_iterable)

def assert_non_null_values(*values, abort_code: int = 400):
    print("Assert ", values, "for None value: ", end="")
    if values and not all(values):
        print("Failed")
        abort(abort_code)
    print("Passed")


def assert_datetime(value: str, abort_code: int = 400):
    print("Assert datetime:", value)
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except ValueError as e:
        print("Assert datetime:", e)
        abort(abort_code)

def assert_date(value: str, abort_code: int = 400):
    print("Assert date:", value)
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError as e:
        print("Assert date:", e)
        abort(abort_code)

def try_date(value: Optional[str], default: date) -> date:
    print("Try date:", value)
    if value is None:
        print("Try date: Defaulting to", default)
        return default
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError as e:
        print("Try date:", e)
    print("Try date: Defaulting to", default)
    return default

def assert_enum(e, value: str, abort_code: int = 400):
    print("Assert enum (%r):" % e._value2member_map_, value)
    if not e._value2member_map_.get(value):
        abort(abort_code)
    return e._value2member_map_.get(value)


def assert_color(value: str):
    print("Assert color:", value)
    # FIXME make assertion
    return value[1:]

def assert_int(value: str, r: Optional[Iterable[int]] = None, abort_code: int = 400):
    print("Assert int:", value)
    try:
        v = int(value)
    except ValueError as e:
        print("Assert int:", e)
        abort(abort_code)

    if r is not None and v not in r:
        print("Assert int range %r failed" % r)
        abort(abort_code)

    return v
