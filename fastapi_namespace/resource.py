from abc import ABCMeta, abstractmethod
from typing import Sequence, Callable, Any, Literal
from fastapi.params import Depends
from inspect import (
    Parameter,
    Signature,
    signature,
    iscoroutinefunction
)
from .typings import MethodHandler, MethodType
from .utils import gen_op_id

def resource_dependant_name(key: str) -> str:
    return f'{key}_dependencies'

class Resource(metaclass=ABCMeta):
    global_dependencies: Sequence[Depends]
    get_dependencies: Sequence[Depends]
    post_dependencies: Sequence[Depends]
    put_dependencies: Sequence[Depends]
    delete_dependencies: Sequence[Depends]
    options_dependencies: Sequence[Depends]
    head_dependencies: Sequence[Depends]
    patch_dependencies: Sequence[Depends]
    trace_dependencies: Sequence[Depends]

    def __init__(self):
        self._init = False


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
            return method_handler(**kwargs)

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
        method_dependencies.reverse()
        global_dependencies = getattr(self, resource_dependant_name('global'), [])
        global_dependencies.reverse()

        method_dependencies.extend(global_dependencies)

        for depends in method_dependencies:
            method_func = self.get_dependant(method_func, depends)
        return method_func