"""
auth_routes.py — AUTHENTICATION endpoints.

POST /api/auth/register  create an account (bcrypt hash in cloud DB)
POST /api/auth/login     exchange credentials for a JWT access token
POST /api/auth/logout    stateless logout (client discards the token)
GET  /api/auth/me        who am I? (validates the token)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.cloud.auth_service import hash_password, issue_token, verify_password
from backend.database import get_db
from backend.models import User
from backend.schemas.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from backend.utils.security import CurrentUser

logger = logging.getLogger("diet.auth")
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new account. Password is bcrypt-hashed; never stored raw."""
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Registered account for %s", email)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Verify credentials and issue a signed JWT access token."""
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()

    # Same generic message for unknown email / wrong password (no user enumeration).
    if user is None or not verify_password(payload.password, user.password_hash):
        logger.warning("Failed login attempt for %s", email)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    token = issue_token(user.id, user.email)
    logger.info("Login OK for %s", email)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/logout")
def logout(current: CurrentUser):
    """
    Stateless JWT logout: the server cannot 'un-sign' a token, so the
    client deletes it. (Production systems add short token lifetimes or
    a revocation list — documented in docs/security.md.)
    """
    return {"detail": f"Logged out. Discard your token, {current.name}."}


@router.get("/me", response_model=UserOut)
def me(current: CurrentUser):
    """Returns the authenticated user — the frontend calls this on boot."""
    return current
