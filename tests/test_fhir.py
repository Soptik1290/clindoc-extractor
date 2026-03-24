from app.services.fhir_service import map_to_fhir
from app.models.response import ExtractionResponse, PatientModel, DiagnosisModel, MedicationModel

def test_map_to_fhir_basic():
    extract = ExtractionResponse(
        patient=PatientModel(name="Jan Novak", birth_date="1968-03-15"),
        diagnoses=[DiagnosisModel(code="I63.9", text="CMP")],
        medications=[MedicationModel(name="aspirin", dose="100mg", frequency="1x denne")]
    )
    
    bundle = map_to_fhir(extract)
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"
    
    entries = bundle["entry"]
    assert len(entries) == 3
    
    patient = entries[0]["resource"]
    assert patient["resourceType"] == "Patient"
    assert patient["name"][0]["text"] == "Jan Novak"
    assert patient["birthDate"] == "1968-03-15"
    
    condition = entries[1]["resource"]
    assert condition["resourceType"] == "Condition"
    assert condition["code"]["coding"][0]["code"] == "I63.9"
    assert condition["code"]["coding"][0]["display"] == "CMP"
    
    med = entries[2]["resource"]
    assert med["resourceType"] == "MedicationRequest"
    assert "aspirin 100mg" in med["medicationCodeableConcept"]["text"]
    assert med["dosageInstruction"][0]["text"] == "1x denne"
