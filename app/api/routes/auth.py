from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.schemas import (
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RegisterRequest,
    RegisterResponse,
    UserPublic,
    VerifyEmailRequest,
)
from app.auth.security import decode_access_token
from app.auth.email import build_verification_link, send_verification_email
from app.auth.service import login_user, register_user, verify_email_token
from app.config import settings
from app.database.dependencies import get_db
from app.database.models import User

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _to_public_user(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        email=user.email,
        is_email_verified=user.is_email_verified,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from exc

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user, verification_token = register_user(db, payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    verification_link = build_verification_link(verification_token)
    email_sent = send_verification_email(user.email, verification_link)

    response = RegisterResponse(
        message=(
            "Registration successful. Verification email sent."
            if email_sent
            else "Registration successful. Please verify your email."
        ),
        user_id=user.id,
    )

    response.verification_link = verification_link

    if settings.expose_verification_token:
        response.verification_token = verification_token

    print(f"Verification link: {verification_link}")
    return response


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        user, access_token = login_user(db, payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return LoginResponse(access_token=access_token, user=_to_public_user(user))


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    try:
        verify_email_token(db, payload.token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return MessageResponse(message="Email verified successfully")


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)):
    return _to_public_user(current_user)
