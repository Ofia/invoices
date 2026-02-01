"""
Google OAuth Authentication Service

This module handles the OAuth 2.0 flow with Google for user authentication.

OAuth Flow:
1. User clicks "Login with Google" on frontend
2. Frontend redirects to /auth/google endpoint
3. We generate an authorization URL and redirect user to Google
4. User logs in with Google and approves our app
5. Google redirects back to our callback URL with an authorization code
6. We exchange the code for access tokens
7. We fetch user info from Google (email, name, Google ID)
8. We create/update user in our database
9. We generate our own JWT token and return it to frontend

Security Notes:
- Never expose Client Secret to frontend
- OAuth tokens are stored for Gmail API access (Phase 5)
- Use HTTPS in production for secure token transmission
"""

from typing import Dict, Any, Optional
from urllib.parse import urlencode
import logging
import httpx
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)


def get_google_auth_url() -> str:
    """
    Generate the Google OAuth authorization URL.

    This URL is where we redirect the user to log in with Google.
    Uses Google's OAuth 2.0 endpoints directly.

    Returns:
        Authorization URL string that includes:
        - client_id: Our Google OAuth client ID
        - redirect_uri: Where Google sends user after login
        - scope: Permissions we're requesting (email, profile, Gmail)
        - response_type: 'code' for authorization code flow
        - access_type: 'offline' to get refresh tokens
        - prompt: 'consent' to always show consent screen (ensures refresh token)

    Example:
        >>> url = get_google_auth_url()
        >>> # Returns: "https://accounts.google.com/o/oauth2/v2/auth?client_id=..."
    """
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "scope": " ".join(settings.GOOGLE_OAUTH_SCOPES),
        "response_type": "code",
        "access_type": "offline",  # Request refresh token
        "prompt": "consent"  # Always show consent screen to get refresh token
    }

    # Build query string with proper URL encoding
    query_string = urlencode(params)
    return f"{base_url}?{query_string}"


async def exchange_code_for_token(code: str) -> Dict[str, Any]:
    """
    Exchange authorization code for access token and fetch user info.

    After Google redirects back with a code, we:
    1. Exchange the code for access and refresh tokens
    2. Use the access token to fetch user information from Google

    Args:
        code: Authorization code from Google's callback

    Returns:
        Dictionary containing user info and tokens:
        {
            "email": "user@example.com",
            "name": "John Doe",
            "google_id": "1234567890",
            "picture": "https://...",
            "access_token": "ya29...",
            "refresh_token": "1//..."
        }

    Raises:
        Exception: If token exchange or user info fetch fails
    """
    # Step 1: Exchange authorization code for tokens
    token_url = "https://oauth2.googleapis.com/token"

    token_data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    # Log token exchange initiation without exposing secrets
    logger.info("Initiating token exchange with Google")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Exchange code for tokens
        token_response = await client.post(token_url, data=token_data)

        logger.info(f"Token exchange status: {token_response.status_code}")

        # If error, include Google's error message
        if token_response.status_code != 200:
            try:
                error_json = token_response.json()
                error_code = error_json.get('error', 'unknown')
                error_description = error_json.get('error_description', 'No description')
                logger.error(f"Google token exchange failed: {error_code} - {error_description}")
                raise httpx.HTTPStatusError(
                    f"Token exchange failed: {error_code}",
                    request=token_response.request,
                    response=token_response
                )
            except ValueError:
                logger.error(f"Google token exchange failed with status {token_response.status_code}")
                raise httpx.HTTPStatusError(
                    f"Token exchange failed with status {token_response.status_code}",
                    request=token_response.request,
                    response=token_response
                )

        tokens = token_response.json()

        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        if not access_token:
            raise Exception("No access token received from Google")

        # Step 2: Fetch user information using access token
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}

        userinfo_response = await client.get(userinfo_url, headers=headers)
        userinfo_response.raise_for_status()
        user_info = userinfo_response.json()

        # Return combined user info and tokens
        return {
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "google_id": user_info.get("id"),  # Google user ID
            "picture": user_info.get("picture"),
            "access_token": access_token,
            "refresh_token": refresh_token  # May be None if not first-time auth
        }


def get_or_create_user(
    db: Session,
    google_id: str,
    email: str,
    oauth_token: Optional[str] = None
) -> User:
    """
    Get existing user or create a new one based on Google authentication.

    This function:
    1. Searches for user by Google ID
    2. If found: updates email and OAuth token
    3. If not found: creates new user

    Args:
        db: Database session
        google_id: Google's unique user identifier
        email: User's email from Google
        oauth_token: Optional OAuth access token for Gmail API access

    Returns:
        User object from database

    Example:
        >>> user = get_or_create_user(db, "1234567890", "user@example.com")
        >>> print(user.id, user.email)
        1 user@example.com
    """
    # Try to find existing user by Google ID
    user = db.query(User).filter(User.google_id == google_id).first()

    if user:
        # User exists - update email and OAuth token if changed
        user.email = email
        if oauth_token:
            user.oauth_token = oauth_token
        db.commit()
        db.refresh(user)
    else:
        # Create new user
        user = User(
            email=email,
            google_id=google_id,
            oauth_token=oauth_token
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user
