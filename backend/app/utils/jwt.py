"""
JWT Token Utilities

This module provides functions for creating and validating JWT (JSON Web Token) tokens.
JWTs are used to maintain user sessions after successful OAuth authentication.

Key concepts:
- Tokens are signed with a secret key to prevent tampering
- Tokens include an expiration time for security
- Tokens contain user identification data (user_id, email)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from app.core.config import settings


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with user data and expiration.

    Args:
        data: Dictionary containing user data to encode in the token
              Typically includes: {"user_id": int, "email": str}
        expires_delta: Optional custom expiration time.
                      Defaults to ACCESS_TOKEN_EXPIRE_MINUTES from settings (7 days)

    Returns:
        Encoded JWT token string

    Example:
        >>> token = create_access_token({"user_id": 1, "email": "user@example.com"})
        >>> # Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    to_encode = data.copy()

    # Calculate expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Add expiration to token payload
    to_encode.update({"exp": expire})

    # Encode and sign the token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT access token.

    This function validates the token signature and expiration time.
    If the token is invalid or expired, returns None.

    Args:
        token: JWT token string to decode

    Returns:
        Decoded token payload as dictionary, or None if invalid

    Example:
        >>> payload = decode_access_token(token)
        >>> if payload:
        >>>     user_id = payload.get("user_id")
        >>>     email = payload.get("email")
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        # Token is invalid, expired, or signature doesn't match
        return None


def verify_token(token: str) -> bool:
    """
    Quick verification if a JWT token is valid.

    Args:
        token: JWT token string to verify

    Returns:
        True if token is valid and not expired, False otherwise

    Example:
        >>> if verify_token(token):
        >>>     print("Token is valid")
        >>> else:
        >>>     print("Token is invalid or expired")
    """
    payload = decode_access_token(token)
    return payload is not None
