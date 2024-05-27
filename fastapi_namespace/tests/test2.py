from fastapi_namespace.mixins.token import OpaqueTokenMixin
from fastapi_namespace.mixins.token.typings import UserIdentify
from fastapi_namespace import Namespace
from fastapi_redis import FastAPIAsyncRedis
from fastapi_redis.types import AsyncRedisClient
from fastapi import Depends
from typing import Literal
import asyncio
redis = FastAPIAsyncRedis()


namespace = Namespace(
    prefix="/t",
)

@namespace.route('')
class Root(OpaqueTokenMixin):
    access_token_limit = 10
    refresh_token_limit = 10
    access_token_expire = 10
    @namespace.doc(summary="가져오기 토큰 테스트")
    async def get(
            self,
            type: Literal["ACCESS", "REFRESH"],
            identify: UserIdentify,
            rd: AsyncRedisClient = Depends(redis.get_connection),
    ):
        return await self._get_user_type_tokens(rd, identify, type)

    @namespace.doc(summary="토큰 만들기 테스트")
    async def post(
            self,
            identify: UserIdentify,
            rd: AsyncRedisClient = Depends(redis.get_connection)
    ):
        access_token, refresh_token = await asyncio.gather(
            self.create_access_token(rd=rd, identify=identify, payload={'a': "123123123"}),
            self.create_refresh_token(rd=rd, identify=identify, payload={'a': "123123123"}),
        )
        return access_token, refresh_token

    @namespace.doc(summary="토큰 삭제 테스트")
    async def delete(
            self,
            type: Literal["ACCESS", "REFRESH"],
            identify: UserIdentify,
            rd: AsyncRedisClient = Depends(redis.get_connection)
    ):
        a = await self._abort_user_type_token(rd=rd, identify=identify, type=type, user_tokens=None)











from fastapi import FastAPI
app = FastAPI()
app.include_router(namespace)


if __name__ == "__main__":
    from uvicorn import run
    run(
        app=app,
        port=23457
    )
