from fastapi_namespace.mixins import MixinBase
from secrets import token_urlsafe
from uuid import uuid4
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline
from typing import (
    TypedDict,
    Literal,
    Callable,
    Sequence,
    Iterable,
    NewType
)
from orjson import loads, dumps
from functools import partial
from fastapi import Depends
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi.exceptions import HTTPException
from fastapi.security.utils import get_authorization_scheme_param
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

TokenType = Literal['ACCESS', 'REFRESH']
AsyncRedisClient: Redis = NewType('AsyncRedisClient', Redis)
AsyncPipeline: Pipeline = NewType('AsyncPipeline', Pipeline)

class TokenPayload(TypedDict):
    jti: str
    identify: str | int

class TokenInfo(TypedDict):
    expires_in: int
    payload: TokenPayload

class Token(TypedDict):
    token: str
    expires_in: int
    payload: TokenPayload
    jti: str

class OAuth2Class(OAuth2AuthorizationCodeBearer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def __call__(self, request: Request) -> str | None:
        authorization = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None  # pragma: nocover
        return param


class OpaqueMixin(MixinBase):
    # """
    # Attributes:
    #     access_token_limit: default 1
    #     refresh_token_limit: default 1
    #     access_token_expire: default 3600
    #     refresh_token_expire: default 129600
    #     user_access_token_key: default user_access_token
    #     user_refresh_token_key: default user_refresh_token
    #     access_token_key: default access_token
    #     refresh_token_key: default refresh_token
    # """
    access_token_limit: int = 1
    refresh_token_limit: int = 1
    access_token_expire: int = 3600
    refresh_token_expire: int = 129600
    user_access_token_key: str = 'user_access_token'
    user_refresh_token_key: str = 'user_refresh_token'
    access_token_key: str = 'access_token'
    refresh_token_key: str = 'refresh_token'
    oauth2_route: list[Literal['get', 'post']] = []
    oauth2_class: Callable = None

    def __init__(self):
        if self.oauth2_class is not None:
            for i in self.oauth2_route:
                getattr(self, f'add_{i}_depends')(Depends(self.oauth2_class))

    def create_token(self) -> str:
        return token_urlsafe(48)

    def _get_access_token_key(self, token: str) -> str:
        """
        Args:
            token: 토큰

        Returns:
            {self.access_token_key}/{token}
        """
        return f"{self.access_token_key}/{token}"

    def _get_refresh_token_key(self, token: str) -> str:
        """
        Args:
            token: 토큰

        Returns:
            {self.refresh_token_key}/{token}
        """
        return f"{self.refresh_token_key}/{token}"

    def _get_user_access_token_key(self, user_id: str) -> str:
        return f"{self.user_access_token_key}/{user_id}"

    def _get_user_refresh_token_key(self, user_id: str) -> str:
        return f'{self.user_refresh_token_key}/{user_id}'

    def _get_token_key_handler(
            self,
            type: TokenType
    ) -> Callable[[str], str]:
        if type == 'ACCESS':
            return self._get_access_token_key
        elif type == 'REFRESH':
            return self._get_refresh_token_key

    def _get_user_token_key_handler(
            self,
            type: TokenType
    ) -> Callable[[str], str]:
        if type == 'ACCESS':
            return self._get_user_access_token_key
        elif type == 'REFRESH':
            return self._get_user_refresh_token_key

    async def _manage_user_token(
            self,
            rd: AsyncRedisClient,
            user_token_key: str
    ):
        async def wrap(pipe: AsyncPipeline, key: str):
            if len((tokens := await pipe.smembers(key))) == 0:
                return
            await pipe.watch(*tokens)
            tokens_for_delete = [i async for i in (await pipe.exists(i) for i in tokens) if i == 0]
            if len(tokens_for_delete) == 0:
                return
            pipe.multi()
            _: AsyncPipeline = pipe.srem(key, *tokens_for_delete)

        await rd.transaction(
            partial(wrap, key=user_token_key),
            user_token_key
        )

    async def _manage_user_token_count(
            self,
            rd: AsyncRedisClient,
            user_token_key: str,
            limit: int
    ) -> None:
        async def wrap(pipe: AsyncPipeline, key: str, limit: int) -> None:
            if len((tokens := await pipe.smembers(key))) == 0:
                return
            await pipe.watch(*tokens)
            token_count = len(tokens)

            if token_count >= limit:
                delete_count = limit - token_count + 1  # 무조건 음수
                delete_tokens = [(i, await pipe.ttl(i)) for i in tokens]
                delete_tokens.sort(key=lambda x: x[1])
                delete_tokens = delete_tokens[:delete_count]
                pipe.multi()
                _: AsyncPipeline = pipe.delete(*(d := [i[0] for i in delete_tokens]))
                _: AsyncPipeline = pipe.srem(key, *d)
            return

        await rd.transaction(
            partial(wrap, key=user_token_key, limit=limit),
            user_token_key
        )

    async def _create_type_token(
            self,
            rd: AsyncRedisClient,
            payload: TokenPayload,
            type: TokenType,
            save: bool = True,
    ) -> Token:
        if type == 'ACCESS':
            get_token_key = self._get_access_token_key
            get_user_token_key = self._get_user_access_token_key
            token_limit = self.access_token_limit
            token_expire = self.access_token_expire
        elif type == 'REFRESH':
            get_token_key = self._get_refresh_token_key
            get_user_token_key = self._get_user_refresh_token_key
            token_limit = self.refresh_token_limit
            token_expire = self.refresh_token_expire
        else:
            raise AttributeError("type muste be ACCESS or REFRESH")

        if not save:
            return self.create_token()

        user_token_key = get_user_token_key(payload["identify"])

        await self._manage_user_token(rd=rd, user_token_key=user_token_key)
        if self.access_token_limit is not None:
            await self._manage_user_token_count(rd=rd, user_token_key=user_token_key, limit=token_limit)

        async def _add(user_token_key: str) -> tuple[str, str]:
            while await rd.sadd(user_token_key, (token_key := get_token_key(token := self.create_token()))) == 0:
                pass
            await rd.expire(user_token_key, token_expire)
            return token, token_key

        async def wrap(pipe: AsyncPipeline, user_token_key: str, token_key: str, payload: str):
            if await pipe.sismember(user_token_key, token_key) == 1:
                pipe.multi()
                _: AsyncPipeline = pipe.set(token_key, payload)
                _: AsyncPipeline = pipe.expire(token_key, token_expire)
                return True
            else:
                return False

        payload = dumps({
            **payload,
            'jti': (jti := uuid4().hex)
        })

        while not await rd.transaction(
                partial(
                    wrap,
                    user_token_key=user_token_key,
                    token_key=(result := await _add(user_token_key))[1],
                    payload=payload
                ),
                *(user_token_key, result[1]),
                value_from_callable=True
        ):
            pass

        ttl = await rd.ttl(result[1])
        return Token(
            token=result[0],
            expires_in=ttl,
            jti=jti
        )

    async def create_access_token(
            self,
            payload: TokenPayload,
            rd: AsyncRedisClient,
            save: bool = True,
    ) -> Token:
        return await self._create_type_token(
            rd=rd,
            payload=payload,
            type="ACCESS",
            save=save
        )

    async def create_refresh_token(
            self,
            payload: TokenPayload,
            rd: AsyncRedisClient,
            save: bool = True,
    ) -> Token:
        return await self._create_type_token(
            rd=rd,
            payload=payload,
            type="REFRESH",
            save=save
        )

    async def get_type_token(
            self,
            rd: AsyncRedisClient,
            token: str,
            type: TokenType = "ACCESS",
    ) -> Token | None:
        if type == "ACCESS":
            get_token_key = self._get_access_token_key
        elif type == 'REFRESH':
            get_token_key = self._get_refresh_token_key

        key = get_token_key(token)

        async def wrap(pipe: AsyncPipeline) -> None | TokenInfo:
            if (token_data := await pipe.get(key)) is None:
                await pipe.unwatch()
                return None

            payload = loads(token_data)
            ttl = await rd.ttl(key)
            return Token(
                token=token,
                expires_in=ttl,
                payload=payload
            )

        return await rd.transaction(wrap, key, value_from_callable=True)

    async def get_access_token(
            self,
            rd: AsyncRedisClient,
            token: str,
    ) -> Token | None:
        return await self.get_type_token(rd=rd, token=token, type="ACCESS")

    async def get_refresh_token(
            self,
            rd: AsyncRedisClient,
            token: str,
    ) -> Token | None:
        if (token := await self.get_type_token(rd=rd, token=token, type="REFRESH")) is None:
            return None
        return token

    async def get_user_type_tokens(
            self,
            rd: AsyncRedisClient,
            user_id: str,
            type: TokenType = "ACCESS",
    ) -> list[Token]:
        if type == "ACCESS":
            get_user_token_key = self._get_user_access_token_key
        elif type == 'REFRESH':
            get_user_token_key = self._get_user_refresh_token_key

        key = get_user_token_key(user_id)

        async def wrap(pipe: AsyncPipeline) -> list[Token]:
            tokens = await pipe.smembers(key)
            if len(tokens) == 0:
                return []

            await pipe.watch(*tokens)
            return [
                Token(
                    token=i.split('/')[1],
                    expires_in=await pipe.ttl(i),
                    payload=loads(await pipe.get(i))
                )
                for i in tokens
            ]

        await self._manage_user_token(rd=rd, user_token_key=key)
        res = await rd.transaction(wrap, key, value_from_callable=True)
        res.sort(key=lambda t: t['expires_in'])
        return res

    async def get_user_access_tokens(
            self,
            rd: AsyncRedisClient,
            user_id: str
    ) -> list[Token]:
        return await self.get_user_type_tokens(
            rd=rd,
            user_id=user_id,
            type="ACCESS"
        )

    async def get_user_refresh_tokens(
            self,
            rd: AsyncRedisClient,
            user_id: str
    ) -> list[Token]:
        return await self.get_user_type_tokens(
            rd=rd,
            user_id=user_id,
            type="REFRESH"
        )

    async def abort_user_type_token(
            self,
            rd: AsyncRedisClient,
            user_id: str,
            type: TokenType,
            user_token: list[str] | None = None,
    ):
        get_token_key = self._get_token_key_handler(type)
        user_token_key = self._get_user_token_key_handler(type)(user_id)

        async def wrap(pipe: AsyncPipeline):
            tokens = await pipe.smembers(user_token_key)
            if len(tokens) == 0:
                return

            if user_token is None or len(user_token) == 0:
                tokens_for_delete = list(tokens)
            else:
                tokens_for_delete = [d for i in user_token if (d := get_token_key(i)) in tokens]

            if len(tokens_for_delete) == 0:
                return

            pipe.multi()
            _: AsyncPipeline = pipe.srem(user_token_key, *tokens_for_delete)
            _: AsyncPipeline = pipe.delete(*tokens_for_delete)
        await rd.transaction(wrap, user_token_key)

    async def abort_user_access_token(
            self,
            rd: AsyncRedisClient,
            user_id: str,
            user_token: str | Sequence[str] | None
    ) -> None:
        if user_token is None:
            await self.abort_user_type_token(rd=rd, user_id=user_id, type='ACCESS')
        elif isinstance(user_token, Iterable):
            await self.abort_user_type_token(rd=rd, user_id=user_id, type='ACCESS', user_token=user_token)
        elif isinstance(user_token, str):
            await self.abort_user_type_token(rd=rd, user_id=user_id, type='ACCESS', user_token=[user_token])

    async def abort_user_refresh_token(
            self,
            rd: AsyncRedisClient,
            user_id: str,
            user_token: str | Sequence[str] | None
    ) -> None:
        if user_token is None:
            await self.abort_user_type_token(rd=rd, user_id=user_id, type='REFRESH')
        elif isinstance(user_token, Iterable):
            await self.abort_user_type_token(rd=rd, user_id=user_id, type='REFRESH', user_token=user_token)
        elif isinstance(user_token, str):
            await self.abort_user_type_token(rd=rd, user_id=user_id, type='REFRESH', user_token=[user_token])
        else:
            raise ValueError('user Token error')

    async def abort_type_token(
            self,
            rd: AsyncRedisClient,
            token: str,
            type: TokenType
    ) -> None:
        token_key = self._get_token_key_handler(type)(token)
        await rd.delete(token_key)

    async def abort_access_token(
            self,
            rd: AsyncRedisClient,
            token: str,
    ) -> None:
        await self.abort_type_token(rd=rd, token=token, type='ACCESS')

    async def abort_refresh_token(
            self,
            rd: AsyncRedisClient,
            token: str,
    ) -> None:
        await self.abort_type_token(rd=rd, token=token, type='REFRESH')