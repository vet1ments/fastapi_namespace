from fastapi import FastAPI, Depends, Path
from fastapi_namespace.namespace import Namespace, Resource
from fastapi_namespace.mixins.token import OpaqueTokenMixin

async def test(b: str, asd: str = Path(...), c:str = "") -> bool:
    print(asd, b, c)
    return 1

namespace = Namespace(
    prefix="/abcv",
    dependencies=[Depends(test)]
)

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi_namespace.mixins import MixinBase

def depend_test4(last: str) -> bool:
    print(last)

class Test(MixinBase):

    global_dependencies = [Depends(depend_test4)]

def depend_test5(last2: str) -> bool:
    print(last2)
class Test2(Test):
    check = 4567
    def __init__(self):
        self.add_global_depends(Depends(self.getAge))

    def getAge(self, age: int):
        print('454545', age)
        print(self.check)

class ItemResponse(BaseModel):
    id: str




app = FastAPI()




def depend_test(arg: str, arg2: str) -> bool:
    print(arg, arg2)

def depend_test2(arg3: str, arg4: str) -> bool:
    print(arg3, arg4)

def depend_get(get: str) -> bool:
    print(get)

def depend_post(post: str) -> bool:
    print(post)

from fastapi import Security

@namespace.route('/{asd}')
class Root(OpaqueTokenMixin):

    global_dependencies = [Depends(depend_test), Depends(depend_test2)]
    get_dependencies = [Depends(depend_get)]
    post_dependencies = [Depends(depend_post)]
    def get(self) -> ItemResponse:
        return ItemResponse(id="1234")

    async def post(self) -> ItemResponse:
        return ItemResponse(id="1234")


app.include_router(namespace)


if __name__ == "__main__":
    from uvicorn import run
    run(
        app=app,
        port=23457
    )
