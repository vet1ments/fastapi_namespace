from starlette.routing import BaseRoute, Match
from starlette.types import ASGIApp, Lifespan, Receive, Scope, Send
from starlette.datastructures import URL
from starlette.responses import RedirectResponse
from starlette._utils import get_route_path
from fastapi import APIRouter
from fastapi.types import (
    IncEx,
)
from fastapi.responses import JSONResponse as ORJSONResponse
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from fastapi import Response
from fastapi.params import Depends

from .resource import Resource
from .types import (
    MethodDocument,
    DecoratedCallable
)
from typing import (
    Optional,
    Callable,
    Sequence,
    Type,
    Any,
    Literal,
)
from .utils import delete_none
from enum import Enum
"""
    실행순서
    route out
    doc out
    doc in
    route in 
    resource set doc

"""

__methods__ = ['get', 'post', 'put', 'delete', 'options', 'head', 'patch', 'trace']


class Namespace(APIRouter):
    def __init__(
            self,
            *,
            prefix: str | None = "",
            tags: list[str | Enum] | None = None,
            dependencies: Sequence[Depends] = None,
            default_response_class: Type[Response] = ORJSONResponse,
            responses: dict[int | str, dict[str, Any]] | None = None,
            callbacks: list[BaseRoute] | None = None,
            routes: list[BaseRoute] | None = None,
            redirect_slashes: bool = True,
            default: ASGIApp | None = None,
            dependency_overrides_provider: Any | None = None,
            route_class: Type[APIRoute] = APIRoute,
            lifespan: Lifespan[Any] | None = None,
            deprecated: bool | None = None,
            include_in_schema: bool = True,
            generate_unique_id_function: Callable[[APIRoute], str] = generate_unique_id,
    ):
        super().__init__(
            prefix=prefix,
            tags=tags,
            dependencies=dependencies,
            default_response_class=default_response_class,
            responses=responses,
            callbacks=callbacks,
            routes=routes,
            redirect_slashes=redirect_slashes,
            default=default,
            dependency_overrides_provider=dependency_overrides_provider,
            route_class=route_class,
            lifespan=lifespan,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            generate_unique_id_function=generate_unique_id_function
        )
        self.get = None
        self.post = None
        self.put = None
        self.delete = None
        self.options = None
        self.head = None
        self.patch = None
        self.trace = None

    def route(
            self,
            path,
            *,
            response_model: Any = None,
            status_code: int | None = None,
            tags: Optional[list[str | Enum]] = None,
            dependencies: Sequence[Depends] | None = None,
            summary: str | None = None,
            description: str | None = None,
            response_description: str = "Successful Response",
            responses: dict[[int | str], dict[str, Any]] | None = None,
            deprecated: bool | None = None,
            operation_id: str | None = None,
            response_model_include: IncEx | None = None,
            response_model_exclude: IncEx | None = None,
            response_model_by_alias: bool = True,
            response_model_exclude_unset: bool = False,
            response_model_exclude_defaults: bool = False,
            response_model_exclude_none: bool = False,
            include_in_schema: bool = True,
            response_class: Type[Response] = ORJSONResponse,
            name: str | None = None,
            callbacks: list[BaseRoute] | None = None,
            openapi_extra: dict[str, Any] | None = None,
            generate_unique_id_function: Callable[[APIRoute], str] = generate_unique_id,
    ) -> Callable[[Resource], Resource]:
        """
        FastAPI APIRoute Class에 deprecated 된 route 함수를 overwriting 하여 사용

        Args:
            path:
            response_model:
            status_code:
            tags: namespace.doc 사용시 append 됨
            dependencies: namespace.doc 사용시 append 됨
            summary:
            description:
            response_description:
            responses:
            deprecated:
            operation_id:
            response_model_include:
            response_model_exclude:
            response_model_by_alias:
            response_model_exclude_unset:
            response_model_exclude_defaults:
            response_model_exclude_none:
            include_in_schema:
            response_class:
            name:
            callbacks: namespace.doc 사용시 append 됨
            openapi_extra:
            generate_unique_id_function:
        """
        def wrap(class_: Resource) -> Resource:
            instance = class_()
            assert isinstance(instance, Resource), "Instance must be of type Resource"
            for meth in __methods__:
                if not hasattr(instance, meth):
                    continue

                meth_func = getattr(instance, meth)
                self._add_method(
                    path,
                    meth,
                    meth_func,
                    response_model=response_model,
                    status_code=status_code,
                    tags=tags,
                    dependencies=dependencies,
                    summary=summary,
                    description=description,
                    response_description=response_description,
                    responses=responses,
                    deprecated=deprecated,
                    operation_id=operation_id,
                    response_model_include=response_model_include,
                    response_model_exclude=response_model_exclude,
                    response_model_by_alias=response_model_by_alias,
                    response_model_exclude_unset=response_model_exclude_unset,
                    response_model_exclude_defaults=response_model_exclude_defaults,
                    response_model_exclude_none=response_model_exclude_none,
                    include_in_schema=include_in_schema,
                    response_class=response_class,
                    name=name,
                    callbacks=callbacks,
                    openapi_extra=openapi_extra,
                    generate_unique_id_function=generate_unique_id_function
                )
            return class_
        return wrap

    def _add_method(
            self,
            path,
            method: Literal['get', 'post', 'put', 'delete', 'options', 'head', 'patch', 'trace'],
            func,
            *,
            response_model: Any = None,
            status_code: int | None = None,
            tags: Optional[list[str | Enum]] = None,
            dependencies: Sequence[Depends] | None = None,
            summary: str | None = None,
            description: str | None = None,
            response_description: str = "Successful Response",
            responses: dict[[int | str], dict[str, Any]] | None = None,
            deprecated: bool | None = None,
            operation_id: str | None = None,
            response_model_include: IncEx | None = None,
            response_model_exclude: IncEx | None = None,
            response_model_by_alias: bool = True,
            response_model_exclude_unset: bool = False,
            response_model_exclude_defaults: bool = False,
            response_model_exclude_none: bool = False,
            include_in_schema: bool = True,
            response_class: Type[Response] = ORJSONResponse,
            name: str | None = None,
            callbacks: list[BaseRoute] | None = None,
            openapi_extra: dict[str, Any] | None = None,
            generate_unique_id_function: Callable[[APIRoute], str] = generate_unique_id,
    ):
        kwargs: MethodDocument = MethodDocument(
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            responses=responses,
            deprecated=deprecated,
            operation_id=operation_id,
            response_model_include=response_model_include,
            response_model_exclude=response_model_exclude,
            response_model_by_alias=response_model_by_alias,
            response_model_exclude_unset=response_model_exclude_unset,
            response_model_exclude_defaults=response_model_exclude_defaults,
            response_model_exclude_none=response_model_exclude_none,
            include_in_schema=include_in_schema,
            response_class=response_class,
            name=name,
            callbacks=callbacks,
            openapi_extra=openapi_extra,
            generate_unique_id_function=generate_unique_id_function
        )
        #
        if hasattr(func.__func__, "__meth_doc__"):
            doc: MethodDocument = func.__func__.__meth_doc__
            if doc.get("dependencies") is not None and dependencies is not None:
                doc["dependencies"] = [*dependencies, *doc["dependencies"]]
            if doc.get("callbacks") is not None and callbacks is not None:
                doc["callbacks"] = [*callbacks, *doc["callbacks"]]
            if doc.get("tags") is not None and tags is not None:
                doc["tags"] = [*tags, *doc["tags"]]
            kwargs.update({
                **doc,
            })
        default_summary = f"{func.__self__.__class__.__name__}_{func.__name__}"
        kwargs.update({
            "summary": default_summary if (summary := kwargs.get("summary", None)) is None else f"{summary} {default_summary}"
        })
        func.__func__.__meth_doc__ = delete_none(kwargs)

        new_func = func.__self__.get_method_handler(
            func
        )
        self.add_api_route(
            path=path,
            endpoint=new_func,
            methods=[method.upper()],
            **func.__func__.__meth_doc__
        )

    def doc(
            self,
            summary: str | None = None,
            description: str | None = None,
            name: str | None = None,
            tags: Optional[list[str | Enum]] = None,
            dependencies: Sequence[Depends] | None = None,
            callbacks: list[BaseRoute] | None = None,
            response_model: Any = None,
            status_code: int | None = None,
            response_description: str = "Successful Response",
            responses: dict[[int | str], dict[str, Any]] | None = None,
            deprecated: bool | None = None,
            operation_id: str | None = None,
            response_model_include: IncEx | None = None,
            response_model_exclude: IncEx | None = None,
            response_model_by_alias: bool = True,
            response_model_exclude_unset: bool = False,
            response_model_exclude_defaults: bool = False,
            response_model_exclude_none: bool = False,
            include_in_schema: bool = True,
            response_class: Type[Response] = ORJSONResponse,
            openapi_extra: dict[str, Any] | None = None,
            generate_unique_id_function: Callable[[APIRoute], str] = generate_unique_id,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        tags = tags or []
        dependencies = dependencies or []
        callbacks = callbacks or []

        def wrap(func: DecoratedCallable) -> DecoratedCallable:
            func.__meth_doc__ = MethodDocument(
                response_model=response_model,
                status_code=status_code,
                tags=tags,
                dependencies=dependencies,
                summary=summary,
                description=description,
                response_description=response_description,
                responses=responses,
                deprecated=deprecated,
                operation_id=operation_id,
                response_model_include=response_model_include,
                response_model_exclude=response_model_exclude,
                response_model_by_alias=response_model_by_alias,
                response_model_exclude_unset=response_model_exclude_unset,
                response_model_exclude_defaults=response_model_exclude_defaults,
                response_model_exclude_none=response_model_exclude_none,
                include_in_schema=include_in_schema,
                response_class=response_class,
                name=name,
                callbacks=callbacks,
                openapi_extra=openapi_extra,
                generate_unique_id_function=generate_unique_id_function,
            )
            return func
        return wrap

    @staticmethod
    def get_method_func_name(func) -> str:
        return f"{func.__class__.__name__}_{func.__name__}"
