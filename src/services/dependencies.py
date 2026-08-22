"""FastAPI authentication and authorization dependencies."""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.role import Role
from src.entity.user import User
from src.repository.blacklist import is_blacklisted
from src.repository.users import get_user_by_id
from src.services.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub", ""))
    except (ValueError, TypeError):
        raise credentials_exception
    if await is_blacklisted(db, token):
        raise credentials_exception
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user account")
    return user


async def get_optional_current_user(
    token: str | None = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if token is None:
        return None
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub", ""))
    except (ValueError, TypeError):
        return None
    if await is_blacklisted(db, token):
        return None
    user = await get_user_by_id(db, user_id)
    return user if user is not None and user.is_active else None


def require_roles(*roles: Role) -> Callable:
    async def dependency(user: User = Depends(get_current_active_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency
