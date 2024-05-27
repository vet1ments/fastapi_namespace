from pydantic import TypeAdapter, ValidationError, ConfigDict
from .typings import (
    OpaqueToken as OpaqueToken_,
    OpaqueTokenInfo as OpaqueTokenInfo_,
    JWTToken as JWTToken_,
    JWTTokenInfo as JWTTokenInfo_,
)
from typing import Literal

class OpaqueToken(OpaqueToken_):
    pass
class OpaqueTokenInfo(OpaqueTokenInfo_):
    pass
class JWTToken(JWTToken_):
    pass
class JWTTokenInfo(JWTTokenInfo_):
    pass

def _default_validate(validator: TypeAdapter, data: dict) -> bool:
    try:
        validator.validate_python(data, strict=True)
        return True
    except ValidationError as e:
        return False

def validate_opaque_token(data: dict, extra: Literal['forbid', 'allow', 'ignore'] = 'forbid') -> bool:
    OpaqueToken.__pydantic_config__ = ConfigDict(extra=extra)
    OpaqueTokenValidator = TypeAdapter(OpaqueToken)
    return _default_validate(OpaqueTokenValidator, data)

def validate_opaque_token_info(data: dict, extra: Literal['forbid', 'allow', 'ignore'] = 'forbid') -> bool:
    OpaqueTokenInfo.__pydantic_config__ = ConfigDict(extra=extra)
    OpaqueTokenInfoValidator = TypeAdapter(OpaqueTokenInfo)
    return _default_validate(OpaqueTokenInfoValidator, data)

def validate_jwt_token(data: dict, extra: Literal['forbid', 'allow', 'ignore'] = 'forbid') -> bool:
    JWTToken.__pydantic_config__ = ConfigDict(extra=extra)
    JWTTokenValidator = TypeAdapter(JWTToken)
    return _default_validate(JWTTokenValidator, data)

def validate_jwt_token_info(data: dict, extra: Literal['forbid', 'allow', 'ignore'] = 'forbid') -> bool:
    JWTTokenInfo.__pydantic_config__ = ConfigDict(extra=extra)
    JWTTokenInfoValidator = TypeAdapter(JWTTokenInfo)
    return _default_validate(JWTTokenInfoValidator, data)