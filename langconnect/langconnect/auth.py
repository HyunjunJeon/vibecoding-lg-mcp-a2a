"""Auth to resolve user object."""

from typing import Annotated

from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.authentication import BaseUser

from langconnect import config

security = HTTPBearer()


class AuthenticatedUser(BaseUser):
    """An authenticated user following the Starlette authentication model."""

    def __init__(self, user_id: str, display_name: str) -> None:
        """Initialize the AuthenticatedUser.

        Args:
            user_id: Unique identifier for the user.
            display_name: Display name for the user.
        """
        self.user_id = user_id
        self._display_name = display_name

    @property
    def is_authenticated(self) -> bool:
        """Return True if the user is authenticated."""
        return True

    @property
    def display_name(self) -> str:
        """Return the display name of the user."""
        return self._display_name

    @property
    def identity(self) -> str:
        """Return the identity of the user. This is a unique identifier."""
        return self.user_id


def validate_api_key(api_key: str) -> bool:
    """Validate API key against configured key.

    Args:
        api_key: API key string to validate

    Returns:
        bool: True if API key is valid, False otherwise
    """
    return api_key == config.LANGCONNECT_API_KEY


def resolve_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> AuthenticatedUser | None:
    """Resolve user from the credentials."""
    if credentials.scheme != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")

    if not credentials.credentials:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Simple API key validation
    if validate_api_key(credentials.credentials):
        # Return a default user for API key authentication
        return AuthenticatedUser("api-user", "API User")
    
    raise HTTPException(status_code=401, detail="Invalid API key")
