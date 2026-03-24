from pydantic import BaseModel
from typing import Optional, Dict

class FieldConfidence(BaseModel):
    value: float
    reason: str

class PatientModel(BaseModel):
    name: Optional[str] = None
    birth_date: Optional[str] = None  # ISO 8601: "1968-03-15"

class VitalsModel(BaseModel):
    bp: Optional[str] = None        # "178/95"
    spo2: Optional[str] = None      # "97%"
    hr: Optional[str] = None        # "92 bpm"
    temperature: Optional[str] = None

class DiagnosisModel(BaseModel):
    code: str
    system: str = "ICD-10"
    text: Optional[str] = None
    confidence: Optional[float] = None

class MedicationModel(BaseModel):
    name: str
    dose: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    confidence: Optional[float] = None

class DatesModel(BaseModel):
    admission: Optional[str] = None  # ISO 8601
    discharge: Optional[str] = None

class ExtractionResponse(BaseModel):
    patient: PatientModel = PatientModel()
    vitals: VitalsModel = VitalsModel()
    diagnoses: list[DiagnosisModel] = []
    medications: list[MedicationModel] = []
    dates: DatesModel = DatesModel()
    follow_up: Optional[str] = None
    confidence: Optional[float] = None
    field_confidence: Optional[Dict[str, FieldConfidence]] = None
    warnings: list[str] = []
    extraction_method: str = "unknown"   # "llm" | "regex_fallback" | "hybrid"

class SubmitResponse(BaseModel):
    job_id: str
    status: str = "pending"

class JobResultResponse(BaseModel):
    job_id: str
    status: str  # "pending" | "processing" | "done" | "failed"
    result: Optional[ExtractionResponse] = None
    error: Optional[str] = None
