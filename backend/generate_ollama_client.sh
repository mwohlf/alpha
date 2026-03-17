#!/bin/bash
# Script to generate Ollama Python client from OpenAPI specification

set -e

echo "Generating Ollama Python client from OpenAPI specification..."

# Check if the OpenAPI spec file exists
if [ ! -f "../etc/ollama-service.yaml" ]; then
    echo "Error: OpenAPI spec not found at ../etc/ollama-service.yaml"
    exit 1
fi

# Generate the client
openapi-python-client generate \
    --path ../etc/ollama-service.yaml \
    --config openapi-client-config.yaml

echo "Client generation complete!"
echo ""
echo "Generated client location: ./ollama_client/"
echo ""
echo "To use the Ollama client in your code:"
echo "  from ollama_client import Client"
echo "  client = Client(base_url='http://localhost:11434')"
