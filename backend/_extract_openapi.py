import json
import yaml
from main import app # Import your FastAPI app instance

def save_openapi():
    # Use the internal .openapi() method to get the generated dict
    openapi_schema = app.openapi()

    # Save as YAML (requires 'pyyaml' package)
    with open("../etc/alpha-service.yaml", "w") as file:
        yaml.dump(openapi_schema, file, sort_keys=False)

if __name__ == "__main__":
    save_openapi()