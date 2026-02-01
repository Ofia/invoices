"""
FastAPI Dependencies for Authentication

Dependencies are reusable functions that FastAPI can inject into route handlers.
They're perfect for things like authentication that many routes need.

Usage in routes:
    @router.get("/protected-endpoint")
    async def protected_route(current_user: User = Depends(get_current_user)):
        return {"user_id": current_user.id}

How it works:
1. Dependency extracts JWT token from Authorization header
2. Validates and decodes the token
3. Fetches user from database
4. Returns user object to the route handler
5. If anything fails, raises HTTPException (401 Unauthorized)
"""

from typing import Optional
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.utils.jwt import decode_access_token

logger = logging.getLogger(__name__)


# HTTPBearer scheme extracts Bearer token from Authorization header
# Example header: "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get the current authenticated user.

    This function:
    1. Extracts the JWT token from the Authorization header
    2. Validates and decodes the token
    3. Fetches the user from the database
    4. Returns the User object

    Args:
        credentials: Automatically extracted by FastAPI from Authorization header
        db: Database session (automatically injected)

    Returns:
        User object of the authenticated user

    Raises:
        HTTPException: 401 if token is invalid or user not found

    Usage in route:
        @router.get("/me")
        async def get_me(user: User = Depends(get_current_user)):
            return {"email": user.email}
    """
    # Extract token from credentials
    token = credentials.credentials

    # Decode and validate token
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user_id from token payload
    user_id: Optional[int] = payload.get("user_id")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication dependency.

    Returns the current user if authenticated, None otherwise.
    Useful for endpoints that have different behavior for logged-in vs anonymous users.

    Args:
        credentials: Optional token from Authorization header
        db: Database session

    Returns:
        User object if authenticated, None otherwise

    Usage in route:
        @router.get("/public-endpoint")
        async def public_route(user: Optional[User] = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Hello {user.email}"}
            return {"message": "Hello anonymous user"}
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = decode_access_token(token)

        if payload is None:
            return None

        user_id: Optional[int] = payload.get("user_id")

        if user_id is None:
            return None

        user = db.query(User).filter(User.id == user_id).first()
        return user

    except Exception as e:
        # If anything goes wrong, just return None (don't raise error)
        logger.warning(f"Optional auth failed: {str(e)}")
        return None
