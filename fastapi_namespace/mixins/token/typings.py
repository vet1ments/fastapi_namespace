from redis.asyncio import Redis
from redis.asyncio.client import Pipeline

AsyncRedis = Redis
AsyncPipeline = Pipeline

from typing import (
    Literal,
    NewType,
    Any,
    Union,
    Generic
)
from typing_extensions import (
    TypedDict,
    NotRequired
)

MethodType = Literal["get", "post", "put", "delete", "patch", "head", "options", "trace"]

TokenType = Literal["ACCESS", "REFRESH"]
TokenKey = NewType('TokenKey', str)
UserTokenKey = NewType('UserTokenKey', str)
RawToken = NewType("RawToken", str)

TokenLimit = NewType("TokenLimit", int)
TokenExpire = NewType("TokenExpire", int)
TokenIdentify = NewType("TokenIdentify", int)
TokenPayload = NewType("TokenPayload", int)
UserIdentify = Union[int, str]

class Token(TypedDict):
    payload: TokenPayload
    uid: UserIdentify

class TokenInfo(TypedDict):
    token: RawToken
    expires_in: NotRequired[TokenExpire]

class OpaqueToken(Token):
    idf: TokenIdentify


class OpaqueTokenInfo(TokenInfo, OpaqueToken):
    pass

class JWTToken(Token):
    jti: TokenIdentify

class JWTTokenInfo(TokenInfo, JWTToken):
    pass