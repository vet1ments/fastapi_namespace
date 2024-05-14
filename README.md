# FastAPI Namespace
fastapi 라우팅 관리를 위한 namespace class
## USAGE
```python
from fastapi import FastAPI
from fastapi_namespace import Namespace, Resource

app = FastAPI()
namespace = Namespace()

@namespace.route(summary="test")
class CustomNamespace(Resource):
    
    @namespace.doc(summary="test1")
    def get(self):
        ...
    
    async def post(self):
        ...


if __name__ == "__main__":
    from uvicorn import run
    run(
        app=app
    )
```