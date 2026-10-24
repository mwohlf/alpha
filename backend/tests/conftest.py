import sys
from pathlib import Path

# make backend modules (config, database, ...) importable like in the app
sys.path.insert(0, str(Path(__file__).parent.parent))
