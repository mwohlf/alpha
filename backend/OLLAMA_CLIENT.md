# Ollama Client Integration

This backend integrates with the Ollama service for AI model inference capabilities.

## Getting Started

### Prerequisites

- Ollama service running (default: http://localhost:11434)
- Dependencies installed: `pip install -r requirements.txt`

### Configuration

Set the following environment variables in your `.env` file if needed:

```env
# Ollama Service Configuration
OLLAMA_BASE_URL=http://localhost:11434
```

## Generating the Python Client

The openapi-python-client package can automatically generate a type-safe Python client from the Ollama OpenAPI specification.

### Generate Client

Run the generation script:

```bash
bash generate_ollama_client.sh
```

This will create a `ollama_client/` directory with auto-generated client code.

Alternatively, generate manually:

```bash
openapi-python-client generate \
    --path ../etc/ollama-service.yaml \
    --config openapi-client-config.yaml
```

## Using the Ollama Client

### Direct Client Usage

```python
from ollama_service import get_ollama_client

# Get singleton client instance
client = get_ollama_client()

# List available models
models = client.list_models()

# Generate text
response = client.generate(
    model="llama2",
    prompt="Hello, how are you?",
    temperature=0.7
)

# Generate embeddings
embeddings = client.embed(
    model="nomic-embed-text",
    prompt="Sample text for embedding"
)

# Pull a model
client.pull_model("mistral")

# Get model details
model_info = client.show_model("llama2")
```

### Via FastAPI Endpoints

The backend exposes the following endpoints for Ollama operations:

#### List Models
```http
GET /api/ollama/models
```

Response:
```json
{
  "models": [
    {
      "name": "llama2:latest",
      "modified_at": "2024-01-15T10:30:00Z",
      "size": 3826519040,
      "digest": "sha256:..."
    }
  ]
}
```

#### Generate Text
```http
POST /api/ollama/generate
Content-Type: application/json

{
  "model": "llama2",
  "prompt": "Write a short story about AI",
  "temperature": 0.7,
  "top_k": 40,
  "top_p": 0.9
}
```

#### Generate Embeddings
```http
POST /api/ollama/embed
Content-Type: application/json

{
  "model": "nomic-embed-text",
  "text": "Sample text for embedding"
}
```

#### Pull a Model
```http
POST /api/ollama/pull?model_name=mistral
```

## Architecture

### ollama_service.py
Provides a clean wrapper (`OllamaClient`) around the Ollama HTTP API with:
- Model listing
- Text generation
- Embeddings
- Model management

### Generated Client (ollama_client/)
Auto-generated from `ollama-service.yaml` OpenAPI spec for type-safe API interactions.

## Error Handling

The client includes logging and exception handling:

```python
import logging
from ollama_service import get_ollama_client

logger = logging.getLogger(__name__)

try:
    client = get_ollama_client()
    result = client.generate(model="llama2", prompt="test")
except Exception as e:
    logger.error(f"Ollama error: {e}")
```

## Development

### Update Client

If the `ollama-service.yaml` OpenAPI spec changes, regenerate the client:

```bash
bash generate_ollama_client.sh
```

### Customize Generated Code

The `openapi-client-config.yaml` controls code generation:
- `project_name_override`: Package name
- `output_directory_override`: Where to generate files
- `class_name`: Main client class name

## References

- Ollama API Docs: https://github.com/ollama/ollama/tree/main/docs
- openapi-python-client: https://github.com/openapi-generators/openapi-python-client
- OpenAPI Specification: https://spec.openapis.org/
