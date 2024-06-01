from ..mixinBase import MixinBase
from .typings import (
    TokenLimit,
    TokenKey,
    UserTokenKey,
    TokenExpire,
    MethodType,
    OpaqueToken,
    OpaqueTokenInfo,
    JWTToken,
    JWTTokenInfo,
    TokenType,
    RawToken,
    UserIdentify,
    AsyncRedis,
    AsyncPipeline,
    TokenPayload,
    Token,
)
from typing import (
    Callable,
    Union,
    Awaitable,
    ParamSpec,
    TypeAlias,
    Generic,
    TypeVar,
    Iterable,
    Coroutine,
    Any,
    Optional
)
from abc import abstractmethod
import asyncio
from functools import partial
from orjson import dumps, loads

P = ParamSpec("P")
TI = TypeVar("TI", OpaqueTokenInfo, JWTTokenInfo)
T = TypeVar("T", OpaqueToken, JWTToken)
TokenKeyHandler = Callable[[RawToken], TokenKey]
UserTokenKeyHandler = Callable[[UserIdentify], UserTokenKey]
_validator: TypeAlias = Callable[[dict[str, Any]], bool]
TokenValidator = _validator
TokenInfoValidator = _validator
CallableToken = Callable[..., T]
CallableTokenInfo = Callable[..., TI]


class TokenBaseMixin(Generic[T, TI], MixinBase):
    access_token_limit: TokenLimit | None = 1
    refresh_token_limit: TokenLimit | None = 1
    access_token_expire: TokenExpire = 3600
    refresh_token_expire: TokenExpire = 129600
    user_access_token_key: str = 'user_access_token'
    user_refresh_token_key: str = 'user_refresh_token'
    access_token_key: str = 'access_token'
    refresh_token_key: str = 'refresh_token'
    oauth2_route: list[MethodType] = []
    oauth2_class: Callable = None

    def __init__(
            self,
            token: CallableToken,
            token_info: CallableTokenInfo,
            token_validator: TokenValidator,
            token_info_validator: TokenInfoValidator
    ):
        self._Token = token
        self._TokenInfo = token_info
        self._token_validator = token_validator
        self._token_info_validator = token_info_validator

    @abstractmethod
    def create_token(self, *args, **kwarg) -> RawToken:
        pass

    @abstractmethod
    def _make_token(self, token: Token) -> TI:
        pass

    def _get_access_token_key(self, token: RawToken) -> TokenKey:
        return TokenKey(f"{self.access_token_key}/{token}")

    def _get_refresh_token_key(self, token: RawToken) -> TokenKey:
        return TokenKey(f"{self.refresh_token_key}/{token}")

    def _get_token_key_handler(self, type: TokenType) -> TokenKeyHandler:
        if type == "ACCESS":
            return self._get_access_token_key
        elif type == "REFRESH":
            return self._get_refresh_token_key
        raise ValueError(f"Token type must be ACCESS or REFRESH")

    def _get_user_access_token_key(self, idf: UserIdentify) -> UserTokenKey:
        return UserTokenKey(f"{self.user_access_token_key}/{idf}")

    def _get_user_refresh_token_key(self, idf: UserIdentify) -> UserTokenKey:
        return UserTokenKey(f"{self.user_refresh_token_key}/{idf}")

    def _get_user_token_key_handler(self, type: TokenType) -> UserTokenKeyHandler:
        if type == "ACCESS":
            return self._get_user_access_token_key
        elif type == "REFRESH":
            return self._get_user_refresh_token_key
        raise ValueError(f"Token type must be ACCESS or REFRESH")

    async def _register_token(
            self,
            rd: AsyncRedis,
            key: UserTokenKey,
            token_key_handler: TokenKeyHandler,
            token_expire: TokenExpire,
            **kwargs
    ) -> tuple[RawToken, TokenKey]:
        """``Redis`` 에 토큰 등록

        * class 내부 사용됨

        Args:
            rd: Async Redis Client
            key:
            token_key_handler:
            token_expire: 토큰 만료 시간
            **kwargs: 토큰 만들때 인자로 넘겨줌

        Returns:
            * ``tuple[0]`` = ``RawToken``
            * ``tuple[1]`` = ``TokenKey``
        """

        while await rd.sadd(
                key,
                (
                        token_key := token_key_handler(
                            token := self.create_token(**kwargs)
                        )
                )
        ) == 0:
            pass
        await rd.expire(key, token_expire)
        return token, TokenKey(token_key)

    @staticmethod
    async def _manage_user_token(
            rd: AsyncRedis,
            key: UserTokenKey
    ) -> None:
        """uid로 등록된 토큰을 관리함

        * class 내부 사용

        Args:
            rd: Async Redis client
            key:
        """
        async def wrap(pipe: AsyncPipeline, key: UserTokenKey):
            if len((tokens := await pipe.smembers(key))) == 0:
                return
            await pipe.watch(*tokens)

            async def _gen():
                for i in tokens:
                    yield i, await pipe.exists(i)

            tokens_for_delete = [i[0] async for i in _gen() if i[1] == 0]
            if len(tokens_for_delete) == 0:
                return
            pipe.multi()
            await pipe.srem(key, *tokens_for_delete)

        await rd.transaction(
            partial(wrap, key=key),
            key
        )

    @staticmethod
    async def _manage_user_token_count(
            rd: AsyncRedis,
            key: UserTokenKey,
            limit: TokenLimit
    ) -> None:
        """토큰 갯수 제한시 토큰을 관리함

        * class 내부 사용

        Args:
            rd: Async Redis client
            key: User Token key
            limit: 토큰 제한 갯수
        """

        async def wrap(
                pipe: AsyncPipeline,
                key: UserTokenKey,
                limit: TokenLimit
        ) -> None:
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
                _: Awaitable = pipe.delete(*(d := [i[0] for i in delete_tokens]))
                _: Awaitable = pipe.srem(key, *d)
            return

        await rd.transaction(
            partial(wrap, key=key, limit=limit),
            key
        )

    async def _create_type_token(
            self,
            rd: AsyncRedis,
            payload: TokenPayload,
            identify: UserIdentify,
            type: TokenType,
            **kwargs,
    ) -> TI:
        """토큰 만든 후 Redis에 저장

        * Class 내부 사용
        * 직접 사용 금지 ``create_access_token`` ``create_refresh_token`` 을 사용

        Args:
            rd: Async Redis Client
            payload:
            identify: Redis 내 사용될 uid
            type: ACCESS or REFRESH
            **kwargs: create_token 의 인자로 넘겨줌
        """
        if type == 'ACCESS':
            token_limit = self.access_token_limit
            token_expire = self.access_token_expire
        elif type == 'REFRESH':
            token_limit = self.refresh_token_limit
            token_expire = self.refresh_token_expire
        else:
            raise AttributeError("type must be ACCESS or REFRESH")

        get_token_key = self._get_token_key_handler(type)
        get_user_token_key = self._get_user_token_key_handler(type)

        user_token_key = get_user_token_key(identify)

        # 토큰 갯수 및 존재 여부 관리
        await self._manage_user_token(rd=rd, key=user_token_key)
        if token_limit is not None:
            await self._manage_user_token_count(rd=rd, key=user_token_key, limit=token_limit)

        # 토큰 제작
        async def transaction(
                pipe: AsyncPipeline,
                user_token_key: UserTokenKey,
                token_key: TokenKey,
                token: Token,
                token_expire: TokenExpire
        ) -> bool:
            token = dumps(token)
            if await pipe.sismember(user_token_key, token_key) == 1:
                pipe.multi()
                _: Awaitable = pipe.set(token_key, token)
                _: Awaitable = pipe.expire(token_key, token_expire)
                return True
            else:
                return False

        get_token_info = partial[TI](self._make_token, token=Token(uid=identify, payload=payload))
        get_raw_token_and_token_key = partial[Coroutine[Any, Any, tuple[RawToken, TokenKey]]](
            self._register_token,
            rd=rd,
            key=user_token_key,
            token_key_handler=get_token_key,
            token_expire=token_expire,
            **kwargs
        )
        while not await rd.transaction(
                partial(
                    transaction,
                    user_token_key=user_token_key,
                    token_key=(result := await get_raw_token_and_token_key())[1],
                    token=(token_info := get_token_info()),
                    token_expire=token_expire
                ),
                *(user_token_key, result[1]),
                value_from_callable=True
        ):
            pass

        ttl: int = await rd.ttl(result[1])
        token_info["expires_in"] = ttl
        token_info["token"] = result[0]
        return token_info

    async def create_access_token(
            self,
            rd: AsyncRedis,
            payload: TokenPayload,
            identify: UserIdentify,
            **kwargs
    ) -> TI:
        """
        Args:
            rd:
            payload:
            identify:
            **kwargs: ``create_token`` 인자로 넘어감
        """
        return await self._create_type_token(
            rd=rd,
            payload=payload,
            type="ACCESS",
            identify=identify,
            **kwargs
        )

    async def create_refresh_token(
            self,
            rd: AsyncRedis,
            payload: TokenPayload,
            identify: UserIdentify,
            **kwargs
    ) -> TI:
        """
        Args:
            rd:
            payload:
            identify:
            **kwargs: ``create_token`` 인자로 넘어감
        """
        return await self._create_type_token(
            rd=rd,
            payload=payload,
            type="REFRESH",
            identify=identify,
            **kwargs
        )

    async def get_type_token(
            self,
            rd: AsyncRedis,
            token: RawToken,
            type: TokenType = "ACCESS",
    ) -> Optional[TI]:
        get_token_key = self._get_token_key_handler(type)
        token_key = get_token_key(token)

        async def transaction(
                pipe: AsyncPipeline,
                raw_token: RawToken,
                key: TokenKey
        ) -> Optional[TI]:
            if (__token := await pipe.get(key)) is None:
                await pipe.unwatch()
                return None

            _token = self._Token(**loads(__token))
            if not self._token_validator(_token):
                return None

            ttl = await rd.ttl(key)

            return self._TokenInfo(
                token=raw_token,
                expires_in=ttl,
                **_token
            )

        return await rd.transaction(
            partial(
                transaction,
                raw_token=token,
                key=token_key,
            ),
            token_key,
            value_from_callable=True
        )

    async def get_access_token(
            self,
            rd: AsyncRedis,
            token: RawToken,
    ) -> Optional[TI]:
        return await self.get_type_token(rd=rd, token=token, type="ACCESS")

    async def get_refresh_token(
            self,
            rd: AsyncRedis,
            token: RawToken,
    ) -> Optional[TI]:
        return await self.get_type_token(rd=rd, token=token, type="REFRESH")

    async def _get_user_type_tokens(
            self,
            rd: AsyncRedis,
            identify: UserIdentify,
            type: TokenType = "ACCESS",
    ) -> list[TI]:
        get_token_key = self._get_token_key_handler(type)
        get_user_token_key = self._get_user_token_key_handler(type)

        key = get_user_token_key(identify)

        async def transaction(
                pipe: AsyncPipeline,
                key: UserTokenKey
        ) -> list[TI]:
            tokens = await pipe.smembers(key)
            if len(tokens) == 0:
                return []

            await pipe.watch(*tokens)
            ttl = None
            return [
                self._TokenInfo(
                    token=i.split('/')[1],
                    expires_in=ttl,
                    **token
                )
                for i in tokens if self._token_validator((token := self._Token(**loads(await pipe.get(i))))) and (ttl := await pipe.ttl(i)) > 5
            ]

        await self._manage_user_token(rd=rd, key=key)
        res: list[TI] = await rd.transaction(
            partial(transaction, key=key),
            key,
            value_from_callable=True
        )
        res.sort(key=lambda t: t['expires_in'])

        return res

    async def get_user_access_tokens(
            self,
            rd: AsyncRedis,
            identify: UserIdentify
    ) -> list[TI]:
        return await self._get_user_type_tokens(
            rd=rd,
            identify=identify,
            type="ACCESS"
        )

    async def get_user_refresh_tokens(
            self,
            rd: AsyncRedis,
            identify: UserIdentify
    ) -> list[TI]:
        return await self._get_user_type_tokens(
            rd=rd,
            identify=identify,
            type="REFRESH"
        )

    async def _abort_user_type_token(
            self,
            rd: AsyncRedis,
            identify: UserIdentify,
            type: TokenType,
            user_tokens: list[RawToken] | None = None,
    ) -> None:
        async def transaction(
                pipe: AsyncPipeline,
                key: UserTokenKey,
                get_token_key: TokenKeyHandler,
                user_tokens: list[RawToken] | None = None
        ) -> None:
            tokens = await pipe.smembers(key)
            if len(tokens) == 0:
                return

            if user_tokens is None or len(user_tokens) == 0:
                tokens_for_delete = list(tokens)
            else:
                tokens_for_delete = [d for i in user_tokens if (d := get_token_key(i)) in tokens]

            if len(tokens_for_delete) == 0:
                return

            pipe.multi()
            _: Awaitable = pipe.srem(key, *tokens_for_delete)
            _: Awaitable = pipe.delete(*tokens_for_delete)

        get_token_key = self._get_token_key_handler(type)
        get_user_token_key = self._get_user_token_key_handler(type)
        user_token_key = get_user_token_key(identify)

        await rd.transaction(
            partial(transaction, key=user_token_key, get_token_key=get_token_key, user_tokens=user_tokens),
            user_token_key
        )

    async def abort_user_access_token(
            self,
            rd: AsyncRedis,
            identify: UserIdentify,
            user_tokens: RawToken | Iterable[RawToken] | None = None
    ) -> None:
        default = partial(self._abort_user_type_token, rd=rd, identify=identify, type="ACCESS")
        if user_tokens is None:
            await default()
        elif isinstance(user_tokens, Iterable):
            await default(user_tokens=[i for i in user_tokens])
        elif isinstance(user_tokens, str):
            await default(user_token=[user_tokens])
        else:
            raise ValueError('user Token error')

    async def abort_user_refresh_token(
            self,
            rd: AsyncRedis,
            identify: UserIdentify,
            user_tokens: RawToken | Iterable[RawToken] | None = None
    ) -> None:
        default = partial(self._abort_user_type_token, rd=rd, identify=identify, type="REFRESH")
        if user_tokens is None:
            await default()
        elif isinstance(user_tokens, Iterable):
            await default(user_tokens=[i for i in user_tokens])
        elif isinstance(user_tokens, str):
            await default(user_token=[user_tokens])
        else:
            raise ValueError('user Token error')

    async def abort_token(
            self,
            rd: AsyncRedis,
            token: RawToken,
    ) -> None:
        get_access_token_key = self._get_token_key_handler("ACCESS")
        get_refresh_token_key = self._get_token_key_handler("REFRESH")

        await asyncio.gather(
            rd.delete(get_access_token_key(token)),
            rd.delete(get_refresh_token_key(token))
        )

    async def _abort_type_token(
            self,
            rd: AsyncRedis,
            token: RawToken,
            type: TokenType
    ) -> None:
        token_key = self._get_token_key_handler(type)(token)
        await rd.delete(token_key)

    async def abort_access_token(
            self,
            rd: AsyncRedis,
            token: RawToken,
    ) -> None:
        await self._abort_type_token(rd=rd, token=token, type='ACCESS')

    async def abort_refresh_token(
            self,
            rd: AsyncRedis,
            token: RawToken,
    ) -> None:
        await self._abort_type_token(rd=rd, token=token, type='REFRESH')
