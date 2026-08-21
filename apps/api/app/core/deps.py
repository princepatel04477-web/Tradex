"""FastAPI dependency injection utilities: Database, Redis, and Auth User Context."""

from typing import AsyncGenerator, Dict, Optional
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import AuthenticationError, AuthorizationError
from app.core.security import decode_token

security_bearer = HTTPBearer(auto_error=False)


class CurrentUser:
    def __init__(self, user_id: str, email: str, role: str = "authenticated"):
        self.user_id = user_id
        self.email = email
        self.role = role


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> Optional[CurrentUser]:
    if not credentials or not credentials.credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        email = payload.get("email", "")
        role = payload.get("role", "authenticated")
        if not user_id:
            return None
        return CurrentUser(user_id=user_id, email=email, role=role)
    except AuthenticationError:
        return None


async def get_current_user(
    user: Optional[CurrentUser] = Depends(get_optional_user),
) -> CurrentUser:
    if not user:
        raise AuthenticationError("Authentication required for this operation")
    return user
