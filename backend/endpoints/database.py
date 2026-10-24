from fastapi import APIRouter, Depends

from database.persona_store import seed_personas
from database.session import wipe_db
from endpoints.auth import verify_token
from endpoints.data_models import DatabaseWipeResponse

router = APIRouter(
    prefix="/database", tags=["database"], dependencies=[Depends(verify_token)]
)


@router.post(
    "/wipe",
    summary="Delete all stored data and re-seed the default personas",
    response_model=DatabaseWipeResponse,
    operation_id="wipe_database",
)
async def wipe_database() -> DatabaseWipeResponse:
    deleted = await wipe_db()
    await seed_personas()
    return DatabaseWipeResponse(deleted=deleted)
