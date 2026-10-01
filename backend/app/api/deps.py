import uuid
import time
from typing import Optional, Dict
from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.core.security import decode_access_token
from app.models import User

# In-memory simple sliding-window rate limiter
_request_counts: Dict[str, list] = {}

def rate_limit(max_requests: int = 60, window_seconds: int = 60):
    async def _rate_limiter(request: Request):
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        key = f"{client_ip}:{request.url.path}"
        timestamps = _request_counts.get(key, [])
        # clean older
        timestamps = [t for t in timestamps if now - t < window_seconds]
        if len(timestamps) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait a moment."
            )
        timestamps.append(now)
        _request_counts[key] = timestamps
    return _rate_limiter


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    # 1. Check httpOnly cookie 'access_token'
    token = request.cookies.get("access_token")

    # 2. Fallback to Authorization: Bearer <token>
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject"
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier format"
        )

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists"
        )

    return user
