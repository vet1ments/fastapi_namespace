import asyncio

from ..mixinBase import MixinBase
from .utils import (
    validate_opaque_token,
    validate_opaque_token_info,
    validate_jwt_token,
    validate_jwt_token_info
)
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
from .utils import (
    validate_opaque_token,
    validate_opaque_token_info,
    validate_jwt_token,
    validate_jwt_token_info
)

from abc import abstractmethod
from typing import (
    Callable,
    Union,
    ParamSpec,
    TypeAlias,
    Generic,
    TypeVar,
    Iterable,
    Coroutine
)
from functools import partial
from orjson import dumps, loads

P = ParamSpec("P")
_TokenInfos = Union[OpaqueTokenInfo, JWTTokenInfo]
_Tokens = Union[OpaqueToken, JWTToken]
TI = TypeVar("TI", bound=_TokenInfos)
T = TypeVar("T", bound=_Tokens)
TokenKeyHandler = Callable[[RawToken], TokenKey]
UserTokenKeyHandler: TypeAlias = Callable[[UserIdentify], UserTokenKey]
_validator: TypeAlias = Callable[[dict], bool]
TokenValidator = _validator
TokenInfoValidator = _validator


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
            token: T,
            token_info: TI,
            token_validator: TokenValidator,
            token_info_validator: TokenInfoValidator
    ):
        self._Token: T = token
        self._TokenInfo: TI = token_info
        self._token_validator = token_validator
        self._token_info_validator = token_info_validator

    @abstractmethod
    def create_token(self) -> RawToken:
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

    def _get_user_access_token_key(self, idf: UserIdentify) -> UserTokenKey:
        return UserTokenKey(f"{self.user_access_token_key}/{idf}")

    def _get_user_refresh_token_key(self, idf: UserIdentify) -> UserTokenKey:
        return UserTokenKey(f"{self.user_refresh_token_key}/{idf}")

    def _get_user_token_key_handler(self, type: TokenType) -> UserTokenKeyHandler:
        if type == "ACCESS":
            return self._get_user_access_token_key
        elif type == "REFRESH":
            return self._get_user_refresh_token_key

    async def _regist_token(
            self,
            rd: AsyncRedis,
            key: UserTokenKey,
            token_key_handler: TokenKeyHandler,
            token_expire: TokenExpire,
            **kwargs
    ) -> tuple[RawToken, TokenKey]:
        """
        Redis에 Token 등록
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
        return RawToken(token), TokenKey(token_key)

    async def _manage_user_token(
            self,
            rd: AsyncRedis,
            key: UserTokenKey
    ) -> None:
        """
        이미 지워진 토큰 들을 user token list 에서 삭제함
        """

        async def wrap(pipe: AsyncPipeline, key: UserTokenKey):
            if len((tokens := await pipe.smembers(key))) == 0:
                return
            await pipe.watch(*tokens)
            tokens_for_delete = [i async for i in (await pipe.exists(i) for i in tokens) if i == 0]
            if len(tokens_for_delete) == 0:
                return
            pipe.multi()
            _: AsyncPipeline = pipe.srem(key, *tokens_for_delete)

        await rd.transaction(
            partial(wrap, key=key),
            key
        )

    async def _manage_user_token_count(
            self,
            rd: AsyncRedis,
            key: UserTokenKey,
            limit: TokenLimit
    ) -> None:
        """
        토큰 갯수 제한이 있을때 user token 리스트와 토큰들의 갯수를 관리해줌
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
                _: AsyncPipeline = pipe.delete(*(d := [i[0] for i in delete_tokens]))
                _: AsyncPipeline = pipe.srem(key, *d)
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
        """
        Args:
            rd:
            payload:
            identify:
            type:
            **kwargs: create_token 의 인자로 넘겨줌
        """
        if type == 'ACCESS':
            token_limit = self.access_token_limit
            token_expire = self.access_token_expire
        elif type == 'REFRESH':
            token_limit = self.refresh_token_limit
            token_expire = self.refresh_token_expire
        else:
            raise AttributeError("type muste be ACCESS or REFRESH")

        get_token_key = self._get_token_key_handler(type)
        get_user_token_key = self._get_user_token_key_handler(type)

        user_token_key: UserTokenKey = get_user_token_key(identify)

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
                _: AsyncPipeline = pipe.set(token_key, token)
                _: AsyncPipeline = pipe.expire(token_key, token_expire)
                return True
            else:
                return False

        get_raw_token_and_token_key = partial(
            self._regist_token,
            rd=rd,
            key=user_token_key,
            token_key_handler=get_token_key,
            token_expire=token_expire,
            **kwargs
        )
        get_token_info = partial(self._make_token, token=Token(uid=identify, payload=payload))
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

        ttl = await rd.ttl(result[1])
        token_info: TI
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
            **kwargs: create token의 인자로 넘어감
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
            **kwargs: create token의 인자로 넘어감
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
    ) -> TI | None:
        get_token_key = self._get_token_key_handler(type)
        token_key = get_token_key(token)

        async def transaction(
                pipe: AsyncPipeline,
                raw_token: RawToken,
                key: TokenKey
        ) -> TI | None:
            if (_token := await pipe.get(key)) is None:
                await pipe.unwatch()
                return None

            token = self._Token(**loads(_token))
            if not self._token_validator(token):
                return None

            ttl = await rd.ttl(key)

            return self._TokenInfo(
                token=raw_token,
                expires_in=ttl,
                **token
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
    ) -> TI | None:
        return await self.get_type_token(rd=rd, token=token, type="ACCESS")

    async def get_refresh_token(
            self,
            rd: AsyncRedis,
            token: RawToken,
    ) -> TI | None:
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

            return [self._TokenInfo(
                token=i.split('/')[1],
                expires_in=await pipe.ttl(i),
                **token
            )
            for i in tokens if self._token_validator((token := self._Token(**loads(await pipe.get(i)))))]

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
            _: AsyncPipeline = pipe.srem(key, *tokens_for_delete)
            _: AsyncPipeline = pipe.delete(*tokens_for_delete)

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