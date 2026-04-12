import secrets
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from config import settings
from endpoints.data_models import LoginRequest, TokenResponse

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(_security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(UTC) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


router = APIRouter(tags=["auth"])


def _verify_password(plain: str, stored: str) -> bool:
    """Accept either a bcrypt hash (production) or plain text (development)."""
    if stored.startswith("$2"):
        return _pwd_context.verify(plain, stored)
    return secrets.compare_digest(plain, stored)


@router.post("/auth/login", response_model=TokenResponse, operation_id="login")
def login(body: LoginRequest) -> TokenResponse:
    if body.username != settings.LOGIN_USERNAME or not _verify_password(
        body.password, settings.LOGIN_PASSWORD
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    return TokenResponse(access_token=_create_access_token({"sub": body.username}))
