"""
Authentication API Routes

This module defines the authentication endpoints for the application.

Endpoints:
- GET /auth/google - Initiates Google OAuth flow
- GET /auth/google/callback - Handles Google's OAuth callback
- GET /auth/me - Returns current user info (protected endpoint)

OAuth Flow Sequence:
1. Frontend: User clicks "Login with Google"
2. Frontend: Redirects to GET /auth/google
3. Backend: Generates Google OAuth URL and redirects user
4. Google: User logs in and approves permissions
5. Google: Redirects to GET /auth/google/callback?code=...
6. Backend: Exchanges code for tokens, gets user info, creates/updates user
7. Backend: Generates JWT token
8. Backend: Returns TokenResponse with JWT and user info
9. Frontend: Stores JWT in localStorage/cookie
10. Frontend: Includes JWT in Authorization header for all future requests
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import logging
import httpx
from app.core.database import get_db
from app.core.config import settings
from app.api.schemas import TokenResponse, UserResponse
from app.api.dependencies import get_current_user
from app.services.auth import get_google_auth_url, exchange_code_for_token, get_or_create_user
from app.utils.jwt import create_access_token

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/google")
async def google_login():
    """
    Initiate Google OAuth login flow.

    This endpoint generates a Google OAuth authorization URL and redirects
    the user to Google's login page.

    Returns:
        RedirectResponse to Google's OAuth authorization page

    Example:
        GET /auth/google
        -> Redirects to: https://accounts.google.com/o/oauth2/v2/auth?client_id=...
    """
    try:
        # Generate Google OAuth authorization URL
        authorization_url = get_google_auth_url()

        # Redirect user to Google login page
        return RedirectResponse(url=authorization_url, status_code=302)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate Google OAuth: {str(e)}"
        )


@router.get("/google/callback")
async def google_callback(
    code: str,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback.

    After user logs in with Google, Google redirects here with an authorization code.
    We exchange the code for user information and create/update the user in our database.

    Query Parameters:
        code: Authorization code from Google (automatically provided)

    Returns:
        TokenResponse containing JWT access token and user information

    Raises:
        HTTPException: 400 if code exchange fails
        HTTPException: 500 if user creation fails

    Example Response:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIs...",
            "token_type": "bearer",
            "user": {
                "id": 1,
                "email": "user@example.com",
                "google_id": "1234567890",
                "created_at": "2026-01-31T10:00:00"
            }
        }
    """
    try:
        # Exchange authorization code for user info
        user_info = await exchange_code_for_token(code=code)

        # Create or update user in database
        user = get_or_create_user(
            db=db,
            google_id=user_info['google_id'],
            email=user_info['email'],
            oauth_token=user_info.get('access_token'),
            refresh_token=user_info.get('refresh_token')
        )

        # Generate JWT access token for our application
        access_token = create_access_token(
            data={
                "user_id": user.id,
                "email": user.email,
                "google_id": user.google_id
            }
        )

        # Return token and user info
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                google_id=user.google_id,
                created_at=user.created_at
            )
        )

    except httpx.TimeoutException as e:
        logger.error(f"Google OAuth timeout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Google authentication service timed out. Please try again."
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"Google OAuth HTTP error: {e.response.status_code}")
        if e.response.status_code >= 500:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Google authentication service is temporarily unavailable."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authentication failed: Invalid authorization code."
            )
    except Exception as e:
        logger.error(f"Unexpected authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during authentication."
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """
    Get current authenticated user information.

    This is a protected endpoint that requires a valid JWT token.
    It demonstrates how to use the get_current_user dependency.

    Headers:
        Authorization: Bearer <jwt_token>

    Returns:
        UserResponse containing current user information

    Raises:
        HTTPException: 401 if token is invalid or missing

    Example Request:
        GET /auth/me
        Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

    Example Response:
        {
            "id": 1,
            "email": "user@example.com",
            "google_id": "1234567890",
            "created_at": "2026-01-31T10:00:00"
        }
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        google_id=current_user.google_id,
        created_at=current_user.created_at
    )


@router.post("/logout")
async def logout():
    """
    Logout endpoint (token invalidation handled client-side).

    Since we're using stateless JWT tokens, logout is handled on the frontend
    by removing the token from storage (localStorage/cookie).

    In the future, we could implement:
    - Token blacklisting (store revoked tokens in Redis)
    - Short-lived tokens with refresh tokens
    - Token revocation on the database level

    Returns:
        Success message

    Example Response:
        {
            "message": "Logged out successfully. Please remove the token from client storage."
        }
    """
    return {
        "message": "Logged out successfully. Please remove the token from client storage."
    }
