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
TokenInfo
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
from orjson import dumps as _dumps, loads
from .sercurity.base import SecurityBase
from typing import Union
from dataclasses import dataclass, asdict



T = TypeVar("T", bound=Token)
# TI = TypeVar("TI", OpaqueTokenInfo, JWTTokenInfo)
TI = TypeVar("TI", bound=TokenInfo)

TokenKeyHandler = Callable[[RawToken], TokenKey]
UserTokenKeyHandler = Callable[[UserIdentify], UserTokenKey]
_validator: TypeAlias = Callable[[dict[str, Any]], bool]
TokenValidator = _validator
TokenInfoValidator = _validator
# CallableToken = Callable[..., T]
# CallableTokenInfo = Callable[..., TI]
CallableToken = type[T]
CallableTokenInfo = type[TI]

def dumps(data):
    print(data, 'werwer')
    return _dumps(asdict(data))




class TransactionCore:
    @staticmethod
    async def _manage_user_token_transaction(pipe: AsyncPipeline, key: UserTokenKey):
        """
        ``Redis`` 내 토큰 관리

        만료 된 토큰은 ``UserTokenList`` 에서 삭제 함
        """
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

    @staticmethod
    async def _manage_user_token_count_transaction(
            pipe: AsyncPipeline,
            key: UserTokenKey,
            limit: TokenLimit
    ) -> None:
        """``Redis`` 내에 토큰 갯수 관리
        """
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

    @staticmethod
    async def _add_token_transaction(
            pipe: AsyncPipeline,
            user_token_key: UserTokenKey,
            token_key: TokenKey,
            token: Token,
            token_expire: TokenExpire
    ) -> bool:
        """``Redis`` 내에 토큰 등록
        """
        token = dumps(token)
        if await pipe.sismember(user_token_key, token_key) == 1:
            pipe.multi()
            _: Awaitable = pipe.set(token_key, token)
            _: Awaitable = pipe.expire(token_key, token_expire)
            return True
        else:
            return False

    @staticmethod
    async def _get_token_transaction(
            pipe: AsyncPipeline,
            raw_token: RawToken,
            key: TokenKey,
            token: CallableToken,
            token_info: CallableTokenInfo,
            token_validator: TokenValidator,
    ) -> Optional[TI]:
        """``Redis`` 에서 토큰 가져오기
        """
        if (__token := await pipe.get(key)) is None:
            await pipe.unwatch()
            return None

        _token = token(**loads(__token))
        if not token_validator(_token):
            return None

        ttl = await pipe.ttl(key)

        return token_info(
            token=raw_token,
            expires_in=ttl,
            **_token
        )

    @staticmethod
    async def _get_user_tokens_transaction(
            pipe: AsyncPipeline,
            key: UserTokenKey,
            token: CallableToken,
            token_info: CallableTokenInfo,
            token_validator: TokenValidator,
    ) -> list[TI]:
        """``Redis`` 에서 특정 유저의 토큰 가져오기
        """
        tokens = await pipe.smembers(key)
        if len(tokens) == 0:
            return []

        await pipe.watch(*tokens)
        ttl = None
        return [
            token_info(
                token=i.split('/')[1],
                expires_in=ttl,
                **_token
            )
            for i in tokens if token_validator((_token := token(**loads(await pipe.get(i))))) and (ttl := await pipe.ttl(i)) > 5
        ]

    @staticmethod
    async def _abort_user_token_transaction(
            pipe: AsyncPipeline,
            key: UserTokenKey,
            get_token_key: TokenKeyHandler,
            user_tokens: list[RawToken] | None = None
    ) -> None:
        """``Redis`` 에서 특정 유저의 토큰을 취소
        """
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





class TokenBaseMixin(Generic[T, TI], MixinBase, TransactionCore):
    access_token_limit: Optional[TokenLimit] | None = 1
    refresh_token_limit: Optional[TokenLimit] | None = 1
    access_token_expire: Optional[TokenExpire] = 3600
    refresh_token_expire: Optional[TokenExpire] = 129600
    user_access_token_key: Optional[str] = 'user_access_token'
    user_refresh_token_key: Optional[str] = 'user_refresh_token'
    access_token_key: Optional[str] = 'access_token'
    refresh_token_key: Optional[str] = 'refresh_token'
    security_route: Optional[list[MethodType]] = []
    security_class: Optional[SecurityBase] = None

    def __init__(
            self,
            token: type[T],
            token_info: type[TI],
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

    async def _manage_user_token(
            self,
            rd: AsyncRedis,
            key: UserTokenKey
    ) -> None:
        """uid로 등록된 토큰을 관리함

        * class 내부 사용

        Args:
            rd: Async Redis client
            key:
        """
        await rd.transaction(
            partial(self._manage_user_token_transaction, key=key),
            key
        )

    async def _manage_user_token_count(
            self,
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
        await rd.transaction(
            partial(self._manage_user_token_count_transaction, key=key, limit=limit),
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
                    self._add_token_transaction,
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
            type: Optional[TokenType] = None,
    ) -> Optional[TI | tuple[TI, TI]]:
        """
        Returns:
            type == None 이면

            * tuple[0] : ACCESS TOKEN INFO
            * tuple[1] : REFRESH TOKEN INFO
        """
        kwargs = {
            "token": self._Token,
            "token_info": self._TokenInfo,
            "token_validator": self._token_validator,
        }
        if type is None:
            return await asyncio.gather(
                rd.transaction(
                    partial(
                        self._get_token_transaction,
                        raw_token=token,
                        key=(token_key := self._get_token_key_handler("ACCESS")(token)),
                        **kwargs
                    ),
                    token_key,
                    value_from_callable=True
                ),
                rd.transaction(
                    partial(
                        self._get_token_transaction,
                        raw_token=token,
                        key=(token_key := self._get_token_key_handler("REFRESH")(token)),
                        **kwargs
                    ),
                    token_key,
                    value_from_callable=True
                ),
            )
        else:
            get_token_key = self._get_token_key_handler(type)
            token_key = get_token_key(token)
            return await rd.transaction(
                partial(
                    self._get_token_transaction,
                    raw_token=token,
                    key=token_key,
                    **kwargs
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

        await self._manage_user_token(rd=rd, key=key)
        res: list[TI] = await rd.transaction(
            partial(
                self._get_user_tokens_transaction,
                key=key,
                token=self._Token,
                token_info=self._TokenInfo,
                token_validator=self._token_validator,
            ),
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
        get_token_key = self._get_token_key_handler(type)
        get_user_token_key = self._get_user_token_key_handler(type)
        user_token_key = get_user_token_key(identify)

        await rd.transaction(
            partial(self._abort_user_token_transaction, key=user_token_key, get_token_key=get_token_key, user_tokens=user_tokens),
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