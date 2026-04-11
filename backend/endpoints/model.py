from fastapi import APIRouter, Depends

from endpoints.auth import verify_token
from endpoints.deps import get_ollama_manager
from endpoints.models import ModelDeleteResponse, ModelListGetResponse, OllamaModel
from ollama.ollama_client import OllamaClientManager

router = APIRouter()


@router.get("/model/list", summary="List locally available models", response_model=ModelListGetResponse, operation_id="get_model_list", dependencies=[Depends(verify_token)])
async def get_model_list(ollama: OllamaClientManager = Depends(get_ollama_manager)) -> ModelListGetResponse:
    models_data = await ollama.list_models()
    return ModelListGetResponse(models=[OllamaModel(**m) for m in models_data])


@router.delete("/model/delete/{name}", summary="Delete a local model", response_model=ModelDeleteResponse, operation_id="delete_model", dependencies=[Depends(verify_token)])
async def delete_model(name: str, ollama: OllamaClientManager = Depends(get_ollama_manager)) -> ModelDeleteResponse:
    await ollama.delete_model(name)
    return ModelDeleteResponse(deleted=name)


@router.post("/model/add", summary="Pull and add a model from the Ollama registry", response_model=OllamaModel, operation_id="add_model", dependencies=[Depends(verify_token)])
async def add_model(name: str, ollama: OllamaClientManager = Depends(get_ollama_manager)) -> OllamaModel:
    await ollama.pull_model(name)
    models_data = await ollama.list_models()
    model = next((m for m in models_data if m.get("name") == name), None)
    return OllamaModel(**(model or {"name": name}))
