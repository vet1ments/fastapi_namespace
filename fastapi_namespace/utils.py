import string
import secrets
from pydantic import TypeAdapter, ValidationError, ConfigDict
from typing import (
    Any,
    Literal,
    Callable,
    Type,
    TypeVar,
    overload,
    ParamSpec,
    Concatenate
)
from typing_extensions import TypedDict, NotRequired

alphabet = string.ascii_letters


def delete_none(dict_) -> dict:
    return {k: v for k, v in dict_.items() if v is not None}


def gen_op_id(length: int = 15) -> str:
    return ''.join(secrets.choice(alphabet) for i in range(length))


def validate_typeddict(
        typed_dict: type[TypedDict],
        data: dict[str, Any],
        extra: Literal['allow', 'ignore'] = 'forbid',
) -> bool:
    """
    Args:
        typed_dict: TypedDict Class
        data: dict
        extra: extra
    """
    class _ValidateClass(typed_dict): ...

    try:
        _ValidateClass.__pydantic_config__ = ConfigDict(extra=extra)
        TypeAdapter(_ValidateClass).validate_python(data, strict=True)
        return True
    except ValidationError as e:
        print(e)
        return False


def get_typeddict_validator(
        typed_dict: type[TypedDict],
        extra: Literal['allow', 'ignore'] = 'forbid',
        strict: bool = True,
) -> Callable[[dict[str, Any]], bool]:

    class _ValidateClass(typed_dict): pass

    def wrap(
            data: dict[str, Any],
    ) -> bool:
        try:
            _ValidateClass.__pydantic_config__ = ConfigDict(extra=extra)
            TypeAdapter(_ValidateClass).validate_python(data, strict=strict)
            return True
        except ValidationError as e:
            print(e)
            return False
    return wrap


P = ParamSpec("P")
TSelf = TypeVar("TSelf")
TReturn = TypeVar("TReturn")
T0 = TypeVar("T0")
T1 = TypeVar("T1")
T2 = TypeVar("T2")


@overload
def add_args_to_signature(
   to_signature: Callable[Concatenate[TSelf, P], TReturn],
   new_arg_type: Type[T0]
) -> Callable[
   [Callable[..., TReturn]],
   Callable[Concatenate[TSelf, T0, P], TReturn]
]:
   pass


@overload
def add_args_to_signature(
   to_signature: Callable[Concatenate[TSelf, P], TReturn],
   new_arg_type0: Type[T0],
   new_arg_type1: Type[T1],
) -> Callable[
   [Callable[..., TReturn]],
   Callable[Concatenate[TSelf, T0, T1, P], TReturn]
]:
   pass


@overload
def add_args_to_signature(
   to_signature: Callable[Concatenate[TSelf, P], TReturn],
   new_arg_type0: Type[T0],
   new_arg_type1: Type[T1],
   new_arg_type2: Type[T2]
) -> Callable[
   [Callable[..., TReturn]],
   Callable[Concatenate[TSelf, T0, T1, P], TReturn]
]:
   pass

# repeat if you want to enable adding more parameters...

def add_args_to_signature(
   *_, **__
):
   return lambda f: f
