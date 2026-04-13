from fastapi import APIRouter, Depends, HTTPException, status

from endpoints.auth import verify_token
from endpoints.data_models import PersonaCreateRequest, PersonaResponse, PersonaUpdateRequest
from database.persona_store import create_persona, get_personas, update_persona

router = APIRouter(
    prefix="/persona", tags=["persona"], dependencies=[Depends(verify_token)]
)


@router.get(
    "",
    response_model=list[PersonaResponse],
    operation_id="get_personas",
    summary="List all personas",
)
async def list_personas() -> list[PersonaResponse]:
    return await get_personas()


@router.post(
    "",
    response_model=PersonaResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_persona",
    summary="Create a new persona",
)
async def add_persona(body: PersonaCreateRequest) -> PersonaResponse:
    return await create_persona(name=body.name, content=body.content, is_active=body.is_active)


@router.put(
    "/{persona_id}",
    response_model=PersonaResponse,
    operation_id="update_persona",
    summary="Update a persona",
)
async def edit_persona(persona_id: int, body: PersonaUpdateRequest) -> PersonaResponse:
    persona = await update_persona(
        persona_id=persona_id,
        name=body.name,
        content=body.content,
        is_active=body.is_active,
    )
    if persona is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona not found")
    return persona
