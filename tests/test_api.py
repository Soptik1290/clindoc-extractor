import pytest
from tests.conftest import DIKTAT_A, DIKTAT_B

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_empty_text_returns_400(client):
    response = client.post("/extract", json={"text": ""})
    assert response.status_code == 422

def test_invalid_json_returns_422(client):
    response = client.post("/extract", data="invalid json")
    assert response.status_code == 422

def test_valid_diktat_a_returns_200(client, mock_openai):
    response = client.post("/extract", json={"text": DIKTAT_A})
    assert response.status_code == 200
    assert response.json()["extraction_method"] in ("llm", "hybrid")

def test_valid_diktat_b_returns_200(client, mock_openai):
    response = client.post("/extract", json={"text": DIKTAT_B})
    assert response.status_code == 200

def test_language_auto_detection(client, mock_openai):
    response = client.post("/extract", json={"text": "Tohle je česky napsaný diktát."})
    assert response.status_code == 200

# Edge cases
def test_text_with_no_extractable_data(client, mock_openai):
    text = "Dnes je pěkně venku a svítí slunce. Včera pršelo."
    response = client.post("/extract", json={"text": text})
    assert response.status_code == 200
    data = response.json()
    assert not data["diagnoses"]

def test_very_long_text(client, mock_openai):
    text = "a" * 10000
    response = client.post("/extract", json={"text": text})
    assert response.status_code == 200

def test_mixed_language_text(client, mock_openai):
    text = "Patient feels well. Nemá žádné bolesti. HR is normal."
    response = client.post("/extract", json={"text": text})
    assert response.status_code == 200

def test_multiple_icd_codes(client, mock_openai):
    text = "Diagnozy: G40.9, I21.4 a E11.9"
    response = client.post("/extract", json={"text": text})
    assert response.status_code == 200
