import uuid
from app.models.response import ExtractionResponse

def map_to_fhir(extraction: ExtractionResponse) -> dict:
    patient_id = str(uuid.uuid4())
    
    entries = []
    
    # 1. Patient Resource
    patient_resource = {
        "resourceType": "Patient",
        "id": patient_id,
        "name": [],
    }
    if extraction.patient.name:
        patient_resource["name"].append({"use": "official", "text": extraction.patient.name})
    if extraction.patient.birth_date:
        patient_resource["birthDate"] = extraction.patient.birth_date
        
    entries.append({"resource": patient_resource})
    
    # 2. Condition Resources
    for diag in extraction.diagnoses:
        condition = {
            "resourceType": "Condition",
            "code": {
                "coding": [{
                    "system": "http://hl7.org/fhir/sid/icd-10",
                    "code": diag.code,
                }]
            },
            "subject": {"reference": f"Patient/{patient_id}"}
        }
        if diag.text:
            condition["code"]["coding"][0]["display"] = diag.text
        entries.append({"resource": condition})
        
    # 3. MedicationRequest Resources
    for med in extraction.medications:
        med_req = {
            "resourceType": "MedicationRequest",
            "medicationCodeableConcept": {"text": f"{med.name} {med.dose}" if med.dose else med.name},
            "subject": {"reference": f"Patient/{patient_id}"}
        }
        if med.frequency:
            med_req["dosageInstruction"] = [{"text": med.frequency}]
        entries.append({"resource": med_req})
        
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": entries
    }
    
    return bundle
