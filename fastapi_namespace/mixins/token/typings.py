import uuid

from redis.asyncio import Redis
from redis.asyncio.client import Pipeline
from redis import Redis
AsyncRedis = Redis
"""
Async ``RedisClient``
"""

AsyncPipeline = Pipeline
"""
Async ``RedisClientPipeline``
"""

from typing import (
    Literal,
    NewType,
    Any,
    Union,
    Generic,
    Optional,
    TypeVar,
    TypeAlias
)
from typing_extensions import (
    TypedDict,
    NotRequired
)
from dataclasses import dataclass, field


TokenKey = NewType('TokenKey', str)
"""
토큰 키 **{user token prefix} / {token}** 형태
"""
UserTokenKey = NewType('UserTokenKey', str)
"""
유저 토큰 키 **{user token prefix} / {uid}** 형태
"""

MethodType = Literal["get", "post", "put", "delete", "patch", "head", "options", "trace"]

TokenType = Literal["ACCESS", "REFRESH"]

RawToken = str

TokenLimit = int

TokenExpire = int

TokenIdentify = str

TokenPayload = dict[str, Any]

UserIdentify = Union[int, str]



@dataclass
class Token:
    """토큰 Base

        다른 토큰 Mixin 생성시 이것을 상속 받을 것

        Attributes:
            payload:
                토큰 페이 로드
            uid:
                Redis 에 등록될 때 구분할 uid
        """
    payload: TokenPayload
    uid: UserIdentify


@dataclass
class OpaqueToken(Token):
    idf: TokenIdentify = field(default=lambda x: uuid.uuid4().hex)


@dataclass
class JWTToken(Token):
    jti: TokenIdentify = field(default=lambda x: uuid.uuid4().hex)


T = TypeVar('T', bound=Token)


@dataclass
class TokenInfo(Generic[T]):
    info: T
    token: Optional[RawToken] = ''
    expires_in: Optional[TokenExpire] = 0


@dataclass
class OpaqueTokenInfo(TokenInfo[OpaqueToken]):
    info: OpaqueToken


@dataclass
class JWTTokenInfo(TokenInfo[JWTToken]):
    info: JWTToken



