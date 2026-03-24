import pytest
import asyncio
from app.extraction.regex_extractor import RegexExtractor
from app.core.config import settings
from tests.conftest import DIKTAT_A, DIKTAT_B

@pytest.fixture
def extractor():
    return RegexExtractor()

def run(coro):
    """Helper to run async extraction in sync tests."""
    return asyncio.get_event_loop().run_until_complete(coro)

# Test 1: Diktát A — česky
def test_diktat_a_patient_name(extractor):
    res = run(extractor.extract(DIKTAT_A))
    assert res.patient.name == "Jan Novak"

def test_diktat_a_birth_date(extractor):
    res = run(extractor.extract(DIKTAT_A))
    assert res.patient.birth_date == "1968-03-15"

def test_diktat_a_admission_date(extractor):
    res = run(extractor.extract(DIKTAT_A))
    assert res.dates.admission == "2024-11-12"

def test_diktat_a_icd_code(extractor):
    res = run(extractor.extract(DIKTAT_A))
    assert any(d.code == "I63.9" for d in res.diagnoses)

def test_diktat_a_aspirin(extractor):
    res = run(extractor.extract(DIKTAT_A))
    asp = next(m for m in res.medications if m.name == "aspirin")
    assert "100mg" in asp.dose

def test_diktat_a_atorvastatin(extractor):
    res = run(extractor.extract(DIKTAT_A))
    ator = next(m for m in res.medications if m.name == "atorvastatin")
    assert "40mg" in ator.dose

def test_diktat_a_bp(extractor):
    res = run(extractor.extract(DIKTAT_A))
    assert res.vitals.bp == "178/95"

def test_diktat_a_spo2(extractor):
    res = run(extractor.extract(DIKTAT_A))
    assert res.vitals.spo2 == "97%"


# Test 2: Diktát B — anglicky/smíšeně
def test_diktat_b_patient_name(extractor):
    res = run(extractor.extract(DIKTAT_B))
    assert res.patient.name == "Maria Horakova"

def test_diktat_b_birth_date(extractor):
    res = run(extractor.extract(DIKTAT_B))
    assert res.patient.birth_date == "1975-07-22"

def test_diktat_b_icd_code(extractor):
    res = run(extractor.extract(DIKTAT_B))
    assert any(d.code == "I21.4" for d in res.diagnoses)

def test_diktat_b_heparin(extractor):
    res = run(extractor.extract(DIKTAT_B))
    hep = next(m for m in res.medications if m.name == "heparin")
    assert "5000 IU" in hep.dose

def test_diktat_b_metoprolol(extractor):
    res = run(extractor.extract(DIKTAT_B))
    metO = next(m for m in res.medications if m.name == "metoprolol")
    assert "25mg" in metO.dose

def test_diktat_b_bp(extractor):
    res = run(extractor.extract(DIKTAT_B))
    assert res.vitals.bp == "145/88"

def test_diktat_b_hr(extractor):
    res = run(extractor.extract(DIKTAT_B))
    assert res.vitals.hr == "92 bpm"

def test_diktat_b_spo2(extractor):
    res = run(extractor.extract(DIKTAT_B))
    assert res.vitals.spo2 == "94%"

# Bonus: confidence scoring tests
def test_diktat_a_has_confidence(extractor):
    res = run(extractor.extract(DIKTAT_A))
    assert res.confidence is not None
    assert 0.0 <= res.confidence <= 1.0

def test_diktat_a_has_field_confidence(extractor):
    res = run(extractor.extract(DIKTAT_A))
    assert res.field_confidence is not None
    assert "patient.name" in res.field_confidence
    assert res.field_confidence["patient.name"].value == 0.9

def test_diktat_b_has_confidence(extractor):
    res = run(extractor.extract(DIKTAT_B))
    assert res.confidence is not None
    assert 0.0 <= res.confidence <= 1.0
