import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import create_access_token, hash_password, verify_password
from app.config import settings
from app.database.models import EmailVerificationToken, User


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_email_verification_token(db: Session, user_id: int) -> str:
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.email_verification_token_expire_hours)

    db.add(
        EmailVerificationToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            used_at=None,
        )
    )
    return raw_token


def register_user(db: Session, email: str, password: str) -> tuple[User, str]:
    normalized_email = normalize_email(email)
    existing = db.scalar(select(User).where(User.email == normalized_email))
    if existing:
        raise ValueError("Email already registered")

    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
        is_email_verified=False,
        is_active=True,
    )
    db.add(user)
    db.flush()

    verification_token = create_email_verification_token(db, user.id)
    db.commit()
    db.refresh(user)
    return user, verification_token


def resend_verification_for_user(db: Session, email: str) -> tuple[User, str]:
    normalized_email = normalize_email(email)
    user = db.scalar(select(User).where(User.email == normalized_email))

    if not user:
        raise ValueError("User not found")

    if not user.is_active:
        raise PermissionError("Account is inactive")

    if user.is_email_verified:
        raise ValueError("Email is already verified")

    verification_token = create_email_verification_token(db, user.id)
    db.commit()
    db.refresh(user)
    return user, verification_token


def login_user(db: Session, email: str, password: str) -> tuple[User, str]:
    normalized_email = normalize_email(email)
    user = db.scalar(select(User).where(User.email == normalized_email))

    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")

    if not user.is_active:
        raise PermissionError("Account is inactive")

    if not user.is_email_verified:
        raise PermissionError("Email is not verified")

    access_token = create_access_token(user.id)
    return user, access_token


def verify_email_token(db: Session, token: str) -> User:
    token_hash = _hash_token(token)

    token_row = db.scalar(
        select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash)
    )

    if not token_row:
        raise ValueError("Invalid verification token")

    if token_row.used_at is not None:
        raise ValueError("Verification token already used")

    expires_at = token_row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        raise ValueError("Verification token has expired")

    user = db.get(User, token_row.user_id)
    if not user:
        raise ValueError("User not found for this token")

    token_row.used_at = datetime.now(timezone.utc)
    user.is_email_verified = True

    db.commit()
    db.refresh(user)
    return user
