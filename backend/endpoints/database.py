import shutil

from fastapi import APIRouter, Depends

from config import settings
from database.persona_store import sync_personas
from database.session import wipe_db
from endpoints.auth import verify_token
from endpoints.data_models import DatabaseWipeResponse

router = APIRouter(
    prefix="/database", tags=["database"], dependencies=[Depends(verify_token)]
)


@router.post(
    "/wipe",
    summary="Delete all stored data and media files, re-sync personas from personas/*.txt",
    response_model=DatabaseWipeResponse,
    operation_id="wipe_database",
)
async def wipe_database() -> DatabaseWipeResponse:
    deleted = await wipe_db()
    media_dir = settings.media_path
    deleted["media_files"] = sum(1 for f in media_dir.rglob("*") if f.is_file()) if media_dir.exists() else 0
    shutil.rmtree(media_dir, ignore_errors=True)
    await sync_personas()
    return DatabaseWipeResponse(deleted=deleted)
