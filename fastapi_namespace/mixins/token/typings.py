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


TokenKey = NewType('TokenKey', str)
UserTokenKey = NewType('UserTokenKey', str)

MethodType = Literal["get", "post", "put", "delete", "patch", "head", "options", "trace"]
TokenType = Literal["ACCESS", "REFRESH"]
# RawToken = NewType("RawToken", str)
RawToken = str
# TokenLimit = NewType("TokenLimit", int)
TokenLimit = int
# TokenExpire = NewType("TokenExpire", int)
TokenExpire = int
# TokenIdentify = NewType("TokenIdentify", int)
TokenIdentify = str
# TokenPayload = NewType("TokenPayload", dict[str, Any])
TokenPayload = dict[str, Any]
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
