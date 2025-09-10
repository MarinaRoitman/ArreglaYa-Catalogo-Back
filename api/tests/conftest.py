import pathlib
import sys
import pytest
from fastapi.testclient import TestClient

# Agregamos la carpeta api/ al sys.path
API_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from main import app  # importa main.py dentro de api/

@pytest.fixture(scope="session")
def client():
    return TestClient(app)
