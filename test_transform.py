# test_transform.py
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_basic_transform():
    r = client.post("/transform", json={"text": "Hello world"})
    assert r.status_code == 200
    j = r.json()
    assert j["original"] == "Hello world"
    assert j["normalized"] == "Hello world"
    assert j["length"] == len("Hello world")
    assert j["tokens"] == ["Hello", "world"]
    assert j["word_count"] == 2
    assert "language" not in j

def test_empty_text():
    r = client.post("/transform", json={"text": ""})
    assert r.status_code == 200
    j = r.json()
    assert j["original"] == ""
    assert j["normalized"] == ""
    assert j["length"] == 0
    assert j["tokens"] == []
    assert j["word_count"] == 0

def test_language_preserved():
    r = client.post("/transform", json={"text": "Hola mundo", "language": "spanish"})
    assert r.status_code == 200
    j = r.json()
    assert j["language"] == "spanish"
    assert j["original"] == "Hola mundo"

def test_invalid_missing_text():
    r = client.post("/transform", json={})
    assert r.status_code == 422  # pydantic validation error from FastAPI

def test_non_string_text():
    r = client.post("/transform", json={"text": 123})
    # pydantic will also treat this as validation error -> 422
    assert r.status_code == 422
