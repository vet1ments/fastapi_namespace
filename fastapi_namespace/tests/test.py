from fastapi import FastAPI, Depends
from fastapi_namespace.namespace import Namespace, Resource

def dpends_base():
    print("depends Base")

namespace = Namespace(
    dependencies=[Depends(dpends_base)]
)

def depends0():
    print("depends0")

def depends1():
    print("depends1")

def depends2():
    print("depends2")

from fastapi import FastAPI
from pydantic import BaseModel
from uvicorn import run


class ItemResponse(BaseModel):
    id: str


@namespace.route(
    "/",
)
class TestResource(Resource):
    # @namespace.doc(
    #     summary="1234",
    #     dependencies=[Depends(depends0)]
    # )
    def get(
            self,
            a: str = Depends(depends2)
    ) -> ItemResponse:
        pass

    def post(self):
        ...

    async def put(self):
        ...


app = FastAPI()

@app.get("/items")
def test() -> ItemResponse:
    return ItemResponse()

app.include_router(namespace)


if __name__ == "__main__":
    from uvicorn import run
    run(
        app=app,
        port=23457
    )
