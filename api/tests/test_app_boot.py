import pathlib, sys

API_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from main import app

def test_app_title():
    assert app.title == "API Desarrollo 2"

def test_openapi_exists(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    data = r.json()
    assert "openapi" in data and "paths" in data
