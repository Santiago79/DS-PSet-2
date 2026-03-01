import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    # Asegura que el paquete `app` sea importable desde los tests
    sys.path.insert(0, str(ROOT_DIR))