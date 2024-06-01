from .tokenBaseMixin import (
    TokenBaseMixin,
    TokenValidator,
    TokenInfoValidator,
    TI
)
from .typings import (
    OpaqueTokenInfo,
    OpaqueToken,
    TokenInfo,
    RawToken,
    Token
)
from fastapi_namespace.utils import get_typeddict_validator
from secrets import token_urlsafe
from uuid import uuid4
from typing_extensions import TypedDict


class OpaqueTokenMixin(TokenBaseMixin[OpaqueToken, OpaqueTokenInfo]):

    def __init__(self):
        token_validator = get_typeddict_validator(OpaqueToken)
        token_info_validator = get_typeddict_validator(OpaqueTokenInfo)

        super().__init__(
            token=OpaqueToken,
            token_info=OpaqueTokenInfo,
            token_validator=token_validator,
            token_info_validator=token_info_validator
        )

    def create_token(self, *args, **kwarg) -> RawToken:
        """
        Returns:
            RawToken: `str`으로 된 토큰
        """
        return token_urlsafe(48)

    def _make_token(self, token: Token) -> OpaqueTokenInfo:
        return OpaqueTokenInfo(
            **token,
            idf=uuid4().hex
        )
