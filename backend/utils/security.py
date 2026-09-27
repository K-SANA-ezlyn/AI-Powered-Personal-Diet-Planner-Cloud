"""
security.py — AUTHORIZATION layer (FastAPI dependencies).

Authentication ("who are you?") happens in cloud/auth_service.py.
This module answers "what are you allowed to do?" on every request:

  get_current_user -> must present a valid Bearer token

Every protected route uses this dependency, which is how the demo
proves one user cannot touch another user's plans or files.
"""

import logging
from typing import Annotated

import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.cloud.auth_service import verify_token
from backend.database import get_db
from backend.models import User

logger = logging.getLogger("diet.security")

bearer_scheme = HTTPBearer(auto_error=False)

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Resolve the User row from the Bearer token, or fail with 401."""
    if credentials is None or not credentials.credentials:
        raise CREDENTIALS_EXCEPTION

    try:
        claims = verify_token(credentials.credentials)
    except pyjwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired — please log in again",
        ) from exc
    except pyjwt.PyJWTError as exc:
        logger.warning("Rejected invalid token: %s", exc)
        raise CREDENTIALS_EXCEPTION from exc

    user_id = claims.get("sub")
    if not user_id:
        raise CREDENTIALS_EXCEPTION

    user = db.get(User, user_id)
    if user is None:
        # Token valid but user deleted — treat as unauthenticated.
        raise CREDENTIALS_EXCEPTION
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
