"""FHIR R4 Pydantic models for Bundle, Patient, Condition, and MedicationRequest."""

from pydantic import BaseModel
from typing import Optional


class FHIRCoding(BaseModel):
    system: str = "http://hl7.org/fhir/sid/icd-10"
    code: str
    display: Optional[str] = None


class FHIRCodeableConcept(BaseModel):
    coding: list[FHIRCoding] = []
    text: Optional[str] = None


class FHIRReference(BaseModel):
    reference: str


class FHIRHumanName(BaseModel):
    use: str = "official"
    text: str


class FHIRDosageInstruction(BaseModel):
    text: str


class FHIRPatient(BaseModel):
    resourceType: str = "Patient"
    id: str
    name: list[FHIRHumanName] = []
    birthDate: Optional[str] = None


class FHIRCondition(BaseModel):
    resourceType: str = "Condition"
    code: FHIRCodeableConcept
    subject: FHIRReference


class FHIRMedicationRequest(BaseModel):
    resourceType: str = "MedicationRequest"
    medicationCodeableConcept: FHIRCodeableConcept
    dosageInstruction: list[FHIRDosageInstruction] = []
    subject: FHIRReference


class FHIRBundleEntry(BaseModel):
    resource: dict  # Flexible to hold Patient, Condition, or MedicationRequest


class FHIRBundle(BaseModel):
    resourceType: str = "Bundle"
    type: str = "collection"
    entry: list[FHIRBundleEntry] = []
