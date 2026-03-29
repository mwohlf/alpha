import sys
import yaml
from main import app # Import your FastAPI app instance

def print_openapi():
    yaml.dump(app.openapi(), sys.stdout, sort_keys=False)

if __name__ == "__main__":
    print_openapi()