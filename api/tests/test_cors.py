import pathlib, sys

API_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from main import ALLOWED_ORIGINS

def test_cors_allows_configured_origin(client):
    origin = ALLOWED_ORIGINS[0]
    r = client.get("/metrics", headers={"Origin": origin})
    assert r.headers.get("access-control-allow-origin") == origin

def test_cors_blocks_unknown_origin(client):
    r = client.get("/metrics", headers={"Origin": "https://totally-unknown.tld"})
    assert "access-control-allow-origin" not in r.headers
