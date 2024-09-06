import uuid

from .typings import TokenPayload, UserIdentify, RawToken, TokenIdentify
from typing import TypeVar, Generic, Optional, Any, Mapping
from orjson import dumps, loads

T = TypeVar('T', bound="Token")


class _Base:
    def dumps(self, except_none: bool = True) -> bytes:
        return dumps(self.as_dict(except_none=except_none))

    def as_dict(self, except_none: bool = True) -> dict[str, Any]:
        dict_ = {}
        for k, v in self.__dict__.items():
            if isinstance(v, _Base):
                dict_[k] = v.as_dict(except_none=except_none)
            else:
                if except_none:
                    if v is not None:
                        dict_[k] = v
        return dict_

    def update(self, data: Mapping[str, Any]):
        for k, v in data.items():
            if (getattr(self, k, None)) is None:
                continue
            setattr(self, k, v)


class Token(_Base):
    def __init__(
            self,
            payload: TokenPayload,
            uid: UserIdentify
    ):
        self.payload = payload
        self.uid = uid


class TokenInfo(Generic[T], _Base):
    def __init__(
            self,
            info: T,
            token: RawToken,
            expires: int = 0,
    ):
        self.info = info
        self.token = token
        self.expires = expires


class OpaqueToken(Token):
    def __init__(
            self,
            payload: TokenPayload,
            uid: UserIdentify,
            idf: TokenIdentify = None
    ):
        super().__init__(
            payload,
            uid,
        )
        self.idf = idf


class OpaqueTokenInfo(TokenInfo[OpaqueToken]):
    pass




