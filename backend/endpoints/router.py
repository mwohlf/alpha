from fastapi import APIRouter

from endpoints.auth import router as auth_router
from endpoints.model import router as model_router
from endpoints.telegram import router as telegram_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(model_router)
router.include_router(telegram_router)
