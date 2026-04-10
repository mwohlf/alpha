import secrets

from fastapi import APIRouter, HTTPException, status

from endpoints.deps import create_access_token, pwd_context
from endpoints.models import LoginRequest, TokenResponse
from config import settings

router = APIRouter(tags=["auth"])


def _verify_password(plain: str, stored: str) -> bool:
    """Accept either a bcrypt hash (production) or plain text (development)."""
    if stored.startswith("$2"):
        return pwd_context.verify(plain, stored)
    return secrets.compare_digest(plain, stored)


@router.post("/auth/login", response_model=TokenResponse, operation_id="login")
def login(body: LoginRequest) -> TokenResponse:
    if body.username != settings.LOGIN_USERNAME or not _verify_password(body.password, settings.LOGIN_PASSWORD):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token({"sub": body.username}))
