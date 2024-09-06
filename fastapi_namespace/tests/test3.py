from fastapi.security.base import SecurityBase as SecurityBase_
from typing import ParamSpec, Callable, TypeVar, Optional, Generic
from dataclasses import dataclass

P = ParamSpec("P")
TBase = TypeVar("TBase")
ValidateFunction = Callable[P, TBase]
T = TypeVar("T", )


class SecurityBase:
    def __init__(self):
        self.validate: Optional[Callable] = None


def validate(a: str):
    print('hi')


sec = SecurityBase()
sec.validate = validate
sec.validate()



def catch_exception(function: Callable[P, T]) -> Callable[P, Optional[T]]:
    def decorator(*args: P.args, **kwargs: P.kwargs) -> Optional[T]:
        try:
            return function(*args, **kwargs)
        except Exception:
            return None
    return decorator

@catch_exception
def div(arg: int) -> float:
    return arg / arg

a = div()
