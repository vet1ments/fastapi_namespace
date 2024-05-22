from typing import Literal, Callable, Any, NewType

MethodType_ = Literal["get", "post", "put", "delete", 'options', 'head', 'patch', 'trace']
MethodType: MethodType_ = NewType('MethodType', MethodType_)
MethodHandler = Callable[[Any], Any]