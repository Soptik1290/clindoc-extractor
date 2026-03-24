import pytest
from fastapi.testclient import TestClient
from app.main import app
import httpx
import json

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_openai(respx_mock):
    mock_content = {
        "patient": {"name": "Mocked Name", "birth_date": "1990-01-01"},
        "vitals": {}, "diagnoses": [], "medications": [], "dates": {}
    }
    
    mock_response = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-5.4-nano",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": json.dumps(mock_content)
            },
            "finish_reason": "stop"
        }]
    }

    respx_mock.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

DIKTAT_A = """Pacient Jan Novak, datum narozeni 15.3.1968, byl prijat 12.11.2024
pro akutni ischemickou CMP s afazii a pravostrannou hemiparezou.
Pridan aspirin 100mg 1x denne a statinova terapie - atorvastatin 40mg.
Krevni tlak pri prijmu 178/95 mmHg, SpO2 97%.
Doporucen rehab program a kontrola u neurologa za 6 tydnu.
Diagnoza: I63.9"""

DIKTAT_B = """Pt. Maria Horakova, DOB 22/07/1975, presented with chest pain and
dyspnoea since yesterday. BP 145/88, HR 92 bpm, SpO2 94%.
ECG: sinus tachycardia. Labs: troponin 0.08 ng/ml, CRP elevated.
Dx: suspected NSTEMI (ICD: I21.4). Started on heparin 5000 IU bolus,
metoprolol 25mg BID. Referred to cardiology, admission recommended."""
