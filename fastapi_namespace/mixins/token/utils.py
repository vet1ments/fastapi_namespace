from pydantic import TypeAdapter, ValidationError
from .typings import OpaqueToken, OpaqueTokenInfo, JWTToken, JWTTokenInfo

OpaqueTokenValidator = TypeAdapter(OpaqueToken)
OpaqueTokenInfoValidator = TypeAdapter(OpaqueTokenInfo)
JWTTokenValidator = TypeAdapter(JWTToken)
JWTTokenInfoValidator = TypeAdapter(JWTTokenInfo)

def _default_validate(validator: TypeAdapter, data: dict) -> bool:
    try:
        validator.validate_python(data)
        return True
    except ValidationError as e:
        return False

def validate_opaque_token(data: dict) -> bool:
    return _default_validate(OpaqueTokenValidator, data)

def validate_opaque_token_info(data: dict) -> bool:
    return _default_validate(OpaqueTokenInfoValidator, data)

def validate_jwt_token(data: dict) -> bool:
    return _default_validate(JWTTokenValidator, data)

def validate_jwt_token_info(data: dict) -> bool:
    return _default_validate(JWTTokenInfoValidator, data)