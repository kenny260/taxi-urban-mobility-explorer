import pytest
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_home(client):
    assert client.get("/").status_code == 200

def test_summary(client):
    r = client.get("/api/stats/summary")
    assert r.status_code == 200

def test_invalid_trip(client):
    r = client.get("/api/trips/999999999")
    assert r.status_code == 404

def test_bad_limit(client):
    r = client.get("/api/trips?limit=abc")
    assert r.status_code == 400

def test_top_routes(client):
    r = client.get("/api/stats/top-routes")
    assert r.status_code == 200

