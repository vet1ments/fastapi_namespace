from .tokenBaseMixin import TokenBaseMixin, TokenValidator, TokenInfoValidator, TI
from .typings import OpaqueTokenInfo, OpaqueToken, TokenInfo, RawToken, Token
from .utils import validate_opaque_token, validate_opaque_token_info

from secrets import token_urlsafe
from uuid import uuid4

class OpaqueTokenMixin(TokenBaseMixin[OpaqueToken, OpaqueTokenInfo]):

    def __init__(self):
        super().__init__(
            token=OpaqueToken,
            token_info=OpaqueTokenInfo,
            token_validator=validate_opaque_token,
            token_info_validator=validate_opaque_token_info
        )

    def create_token(self) -> RawToken:
        return token_urlsafe(48)

    def _make_token(self, token: Token) -> OpaqueTokenInfo:
        OpaqueTokenInfo(
            **token,
            idf=uuid4().hex
        )
