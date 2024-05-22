from abc import ABCMeta, abstractmethod
from typing import Iterable, Callable, Any, Literal
from fastapi.params import Depends
from inspect import (
    Parameter,
    Signature,
    signature,
    iscoroutinefunction
)
from .typings import MethodHandler, MethodType, ResourceProtocol
from .utils import gen_op_id

def resource_dependant_name(key: str) -> str:
    return f'{key}_dependencies'


class Resource:
    global_dependencies: Iterable[Depends]
    get_dependencies: Iterable[Depends]
    post_dependencies: Iterable[Depends]
    put_dependencies: Iterable[Depends]
    delete_dependencies: Iterable[Depends]
    options_dependencies: Iterable[Depends]
    head_dependencies: Iterable[Depends]
    patch_dependencies: Iterable[Depends]
    trace_dependencies: Iterable[Depends]

    def get_dependant(self, method_handler, depends: Depends) -> Callable:
        assert isinstance(depends, Depends), "Dependant must be of type Depends!"
        method_handler_signature = signature(method_handler)
        method_handler_parameters = method_handler_signature.parameters

        op_id = gen_op_id()

        def wrap(**kwargs):
            kwargs.pop(op_id, None)
            return method_handler(**kwargs)

        async def async_wrap(**kwargs):
            kwargs.pop(op_id, None)
            return await method_handler(**kwargs)

        params = [
            Parameter(name=op_id, kind=Parameter.POSITIONAL_OR_KEYWORD, default=depends),
            *method_handler_parameters.values()
        ]

        if iscoroutinefunction(method_handler):
            async_wrap.__signature__ = Signature(
                parameters=params,
                return_annotation=method_handler_signature.return_annotation
            )
            return async_wrap
        else:
            wrap.__signature__ = Signature(
                parameters=params,
                return_annotation=method_handler_signature.return_annotation
            )
            return wrap

    def get_method_handler(
            self,
            method_handler,
    ) -> MethodHandler:
        method_func = method_handler
        method_name: MethodType = method_handler.__name__

        method_dependencies = getattr(self, resource_dependant_name(method_name), [])
        method_dependencies = [*method_dependencies]
        method_dependencies.reverse()
        global_dependencies = getattr(self, resource_dependant_name('global'), [])
        global_dependencies = [*global_dependencies]
        global_dependencies.reverse()

        dependencies = [*method_dependencies, *global_dependencies]

        for depends in dependencies:
            method_func = self.get_dependant(method_func, depends)
        return method_func