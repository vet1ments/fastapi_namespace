from starlette.routing import BaseRoute
from fastapi import Depends, Response
from fastapi.types import IncEx
from fastapi.routing import APIRoute

from typing import TypedDict, NotRequired, Sequence, Type, Any, Callable, TypeVar
from enum import Enum

class MethodDocument(TypedDict):
    response_model: NotRequired[Any]
    status_code: NotRequired[int]
    tags: NotRequired[list[str | Enum]]
    dependencies: NotRequired[Sequence[Depends]]
    summary: NotRequired[str]
    description: NotRequired[str]
    response_description: NotRequired[str]
    responses: NotRequired[dict[[int | str], dict[str, Any]]]
    deprecated: NotRequired[bool]
    operation_id: NotRequired[str]
    response_model_include: NotRequired[IncEx]
    response_model_exclude: NotRequired[IncEx]
    response_model_by_alias: NotRequired[bool]
    response_model_exclude_unset: NotRequired[bool]
    response_model_exclude_defaults: NotRequired[bool]
    response_model_exclude_none: NotRequired[bool]
    include_in_schema: NotRequired[bool]
    response_class: NotRequired[Type[Response]]
    name: NotRequired[str]
    callbacks: NotRequired[list[BaseRoute]]
    openapi_extra: NotRequired[dict[str, Any]]
    generate_unique_id_function: NotRequired[Callable[[APIRoute], str]]


DecoratedCallable = TypeVar("DecoratedCallable", bound=Callable[..., Any])