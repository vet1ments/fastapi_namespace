from fastapi.security.base import SecurityBase as SecurityBase_
from typing import ParamSpec, Callable, TypeVar, Optional

P = ParamSpec("P")
T = TypeVar("T")
ValidateFunction = Callable[P, T]


class SecurityBase(SecurityBase_):...
    # def __init__(self):
    #     self._validate: Optional[ValidateFunction] = None
    #
    # def validate(self, func: ValidateFunction) -> ValidateFunction: