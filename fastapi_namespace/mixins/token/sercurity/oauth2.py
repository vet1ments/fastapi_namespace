from .base import SecurityBase
from fastapi.security import (
    OAuth2 as OAuth2_,
    OAuth2AuthorizationCodeBearer as OAuth2AuthorizationCodeBearer_
)
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.exceptions import HTTPException
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from typing import (
    Union,
    Any,
    Optional,
    Callable,
    TypeVar
)


class OAuth2(SecurityBase, OAuth2_):
    def __init__(
            self,
            flows: Union[OAuthFlowsModel, dict[str, dict[str, Any]]],
            scheme_name: Optional[str] = None,
            description: Optional[str] = None,
            auto_error: bool = True,
    ):
        super().__init__(
            flows=flows,
            scheme_name=scheme_name,
            description=description,
            auto_error=auto_error
        )

    async def __call__(self, request: Request) -> Optional[str]:
        authorization = request.headers.get("Authorization")
        if not authorization:
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
                )
            else:
                return None
        return authorization