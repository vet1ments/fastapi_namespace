from typing import Literal, Callable, Any, NewType, Protocol, Sequence
from fastapi.params import Depends

MethodType_ = Literal["get", "post", "put", "delete", 'options', 'head', 'patch', 'trace']
MethodType: MethodType_ = NewType('MethodType', MethodType_)
MethodHandler = Callable[[Any], Any]

class ResourceProtocol(Protocol):
    global_dependencies: Sequence[Depends]
    get_dependencies: Sequence[Depends]
    post_dependencies: Sequence[Depends]
    put_dependencies: Sequence[Depends]
    delete_dependencies: Sequence[Depends]
    options_dependencies: Sequence[Depends]
    head_dependencies: Sequence[Depends]
    patch_dependencies: Sequence[Depends]
    trace_dependencies: Sequence[Depends]