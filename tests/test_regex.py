import asyncio
from app.extraction.regex_extractor import RegexExtractor

def test_regex_basic():
    extractor = RegexExtractor()
    res = asyncio.get_event_loop().run_until_complete(
        extractor.extract("Pacient Jan Novak 1.1.1990 SpO2 99%")
    )
    assert res.patient.name == "Jan Novak"
    assert res.vitals.spo2 == "99%"

def test_regex_confidence_present():
    extractor = RegexExtractor()
    res = asyncio.get_event_loop().run_until_complete(
        extractor.extract("Pacient Jan Novak SpO2 99% Diagnoza: I63.9")
    )
    assert res.confidence is not None
    assert res.field_confidence is not None
    assert "patient.name" in res.field_confidence
