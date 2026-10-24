from fastapi import APIRouter, Depends

from database.persona_store import sync_personas
from database.session import wipe_db
from endpoints.auth import verify_token
from endpoints.data_models import DatabaseWipeResponse

router = APIRouter(
    prefix="/database", tags=["database"], dependencies=[Depends(verify_token)]
)


@router.post(
    "/wipe",
    summary="Delete all stored data and re-sync personas from personas/*.txt",
    response_model=DatabaseWipeResponse,
    operation_id="wipe_database",
)
async def wipe_database() -> DatabaseWipeResponse:
    deleted = await wipe_db()
    await sync_personas()
    return DatabaseWipeResponse(deleted=deleted)
