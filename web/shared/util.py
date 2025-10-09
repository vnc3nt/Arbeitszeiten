
from typing import Any


class Result:
    def __init__(self, value=None, error=None):
        self.__data = value, error
        self.__error = error is not None

    @property
    def value(self) -> Any:
        return self.__data[1] if self.__error else self.__data[0]

    @property
    def is_value(self) -> bool:
        return not self.__error

    @property
    def is_error(self) -> bool:
        return self.__error


