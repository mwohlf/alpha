from fastapi import APIRouter, Depends

from endpoints.deps import get_ollama_manager, verify_token
from endpoints.models import HealthGetResponse, HelloGetResponse, Model, ModelListGetResponse, ProtectedGetResponse

router = APIRouter()


# this is probably for Kubernetes
@router.get("/health", summary="Health check endpoint", tags=[], response_model=HealthGetResponse, operation_id="get_health")
def get_health() -> HealthGetResponse:
    return HealthGetResponse(status="healthy")


@router.get("/hello", summary="Returns a hello message", tags=[], response_model=HelloGetResponse, operation_id="get_hello")
def get_hello() -> HelloGetResponse:
    return HelloGetResponse(message="Hello from FastAPI")


@router.get("/protected", summary="Protected endpoint requiring JWT token", tags=[], response_model=ProtectedGetResponse, operation_id="get_protected", dependencies=[Depends(verify_token)])
def get_protected() -> ProtectedGetResponse:
    return ProtectedGetResponse(message="This is a protected endpoint")


@router.get("/model/list", summary="Get all models", response_model=ModelListGetResponse, operation_id="get_model_list")
def get_model_list(ollamaManager=Depends(get_ollama_manager)):
    # Example logic: replace with your actual database/state call
    return ModelListGetResponse(models=[Model(uniqueId="llama3", description="Meta Llama 3")])


@router.delete("/model/delete/{id}", summary="Delete a model", response_model=HelloGetResponse, operation_id="delete_model")
def delete_model(id: str, ollamaManager=Depends(get_ollama_manager)):
    # ollamaManager.
    return None


@router.post("/model/add", summary="Download and add a new model", response_model=Model, operation_id="add_model")
def add_model(unique_id: str, ollamaManager=Depends(get_ollama_manager)):
    # Logic to save model...
    model = {unique_id: unique_id}
    return model
