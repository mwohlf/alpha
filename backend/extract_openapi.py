import json
import yaml
from main import app # Import your FastAPI app instance

def save_openapi():
    # Use the internal .openapi() method to get the generated dict
    openapi_schema = app.openapi()
    
    # Save as JSON
    with open("openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
        
    # Save as YAML (requires 'pyyaml' package)
    with open("openapi.yaml", "w") as f:
        yaml.dump(openapi_schema, f, sort_keys=False)

if __name__ == "__main__":
    save_openapi()