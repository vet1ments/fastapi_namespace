from fastapi_namespace.utils import validate_typeddict
from typing_extensions import TypedDict, NotRequired


class Test(TypedDict):
    a: str
    b: str
    c: str


class InheritTest(Test):
    d: str


t = InheritTest(a="a", b='1', d="1", c="3", k="333")

validate = validate_typeddict(InheritTest, t, extra="forbid")
print(validate)
