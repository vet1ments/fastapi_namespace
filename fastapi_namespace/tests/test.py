from fastapi import FastAPI, Depends, Path
from fastapi_namespace.namespace import Namespace, Resource

async def test(b: str, asd: str = Path(...), c:str = "") -> bool:
    print(asd, b, c)
    return 1

namespace = Namespace(
    prefix="/abcv",
    dependencies=[Depends(test)]
)

from fastapi import FastAPI
from pydantic import BaseModel

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

@namespace.route('/{asd}')
class Root(Resource):
    __method_dependant__ = [Depends(depend_test), Depends(depend_test2)]
    __get_dependant__ = [Depends(depend_get)]
    __post_dependant__ = [Depends(depend_post)]
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
