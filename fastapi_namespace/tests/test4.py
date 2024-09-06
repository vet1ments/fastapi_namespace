from fastapi import FastAPI
from fastapi_namespace import Resource
from fastapi_namespace import Namespace
import typing as t
import typing_extensions as tx

namespace = Namespace(prefix='', tags=[''])

class Test(tx.TypedDict):
    test: str
    a: int



app = FastAPI()
app.include_router(namespace)


if __name__ == "__main__":
    from uvicorn import run
    run(
        app=app,
        port=23457
    )