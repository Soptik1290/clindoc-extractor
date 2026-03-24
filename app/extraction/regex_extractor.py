import re
import logging
from typing import Optional
from app.extraction.base import BaseExtractor
from app.models.response import (
    ExtractionResponse, PatientModel, VitalsModel,
    DiagnosisModel, MedicationModel, DatesModel, FieldConfidence,
)
from app.utils.date_parser import normalize_date

logger = logging.getLogger(__name__)

# --- Regex patterns ---

PATIENT_NAME_PATTERNS = [
    (r"[Pp]acient(?:ka)?\s+([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+\s+[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)", 0.9),
    (r"[Pp]t\.\s+([A-Z][a-z]+\s+[A-Z][a-z]+)", 0.9),
]

BIRTH_DATE_PATTERNS = [
    (r"(?:datum narozeni|DOB|nar\.)\s*:?\s*(\d{1,2})[./](\d{1,2})[./](\d{4})", 0.9),
    (r"(\d{1,2})\.(\d{1,2})\.(\d{4})", 0.6),
    (r"(\d{1,2})/(\d{2})/(\d{4})", 0.6),
]

BP_PATTERN = r"(?:BP|[Kk]revni\s+tlak|TK)[^\d]*(\d{2,3})/(\d{2,3})"
SPO2_PATTERN = r"SpO2\s*:?\s*(\d{2,3})\s*%?"
HR_PATTERN = r"(?:HR|[Pp]ulz)[:\s]+(\d{2,3})\s*(?:bpm|/min)?"
ICD_PATTERN = r"\b([A-Z]\d{2}(?:\.\d{1,2})?)\b"

ADMISSION_PATTERNS = [
    (r"(?:byl\s+)?prijat\s+(\d{1,2})\.(\d{1,2})\.(\d{4})", 0.9),
    (r"(?:admission|admitted)\s+(\d{1,2})[./](\d{2})[./](\d{4})", 0.9),
]

MEDICATION_PATTERN = r"([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽa-záčďéěíňóřšťúůýž]+)\s+(\d+(?:\.\d+)?\s*(?:mg|g|IU|mcg|ml))\s*([^,.\n]*?(?=\s+a\s+|\s+-\s+|[,.\n]|$))"


class RegexExtractor(BaseExtractor):
    """Deterministic regex-based clinical data extractor with confidence scoring."""

    async def extract(self, text: str, language: str = "auto") -> ExtractionResponse:
        """Extract clinical data using regex patterns.

        Each pattern match carries a confidence value based on context:
        - Exact match with contextual keyword → 0.9
        - Match without full context → 0.6
        - Ambiguous match → 0.4
        """
        patient = PatientModel()
        vitals = VitalsModel()
        diagnoses: list[DiagnosisModel] = []
        medications: list[MedicationModel] = []
        dates = DatesModel()
        field_confidence: dict[str, FieldConfidence] = {}

        # --- Patient name ---
        for pattern, conf in PATIENT_NAME_PATTERNS:
            match = re.search(pattern, text)
            if match:
                patient.name = match.group(1).strip()
                field_confidence["patient.name"] = FieldConfidence(
                    value=conf, reason="Regex match with contextual keyword"
                )
                break

        # --- Birth date ---
        for pattern, conf in BIRTH_DATE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 3:
                    d, m, y = match.groups()
                    raw_date = f"{d}.{m}.{y}"
                    patient.birth_date = normalize_date(raw_date)
                    field_confidence["patient.birth_date"] = FieldConfidence(
                        value=conf, reason="Regex date match"
                    )
                break

        # --- Admission date ---
        for pattern, conf in ADMISSION_PATTERNS:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 3:
                    d, m, y = match.groups()
                    raw_date = f"{d}.{m}.{y}"
                    dates.admission = normalize_date(raw_date)
                    field_confidence["dates.admission"] = FieldConfidence(
                        value=conf, reason="Regex admission date match"
                    )
                break

        # --- Blood pressure ---
        match_bp = re.search(BP_PATTERN, text)
        if match_bp:
            vitals.bp = f"{match_bp.group(1)}/{match_bp.group(2)}"
            field_confidence["vitals.bp"] = FieldConfidence(
                value=0.9, reason="Regex BP with keyword context"
            )

        # --- SpO2 ---
        match_spo2 = re.search(SPO2_PATTERN, text)
        if match_spo2:
            vitals.spo2 = f"{match_spo2.group(1)}%"
            field_confidence["vitals.spo2"] = FieldConfidence(
                value=0.9, reason="SpO2 keyword context match"
            )

        # --- Heart rate ---
        match_hr = re.search(HR_PATTERN, text)
        if match_hr:
            vitals.hr = f"{match_hr.group(1)} bpm"
            field_confidence["vitals.hr"] = FieldConfidence(
                value=0.9, reason="HR keyword context match"
            )

        # --- ICD Codes ---
        icd_matches = re.finditer(ICD_PATTERN, text)
        seen_codes: set[str] = set()
        for match in icd_matches:
            code = match.group(1)
            if code not in seen_codes:
                # Contextual confidence: higher if near 'Diagnoz' or 'ICD' keyword
                context_window = text[max(0, match.start()-30):match.start()]
                if re.search(r"(?:Diagnoz|ICD|Dx)", context_window, re.IGNORECASE):
                    conf = 0.9
                else:
                    conf = 0.6
                diagnoses.append(DiagnosisModel(code=code, system="ICD-10", confidence=conf))
                seen_codes.add(code)

        if diagnoses:
            avg_conf = sum(d.confidence or 0.0 for d in diagnoses) / len(diagnoses)
            field_confidence["diagnoses"] = FieldConfidence(
                value=round(avg_conf, 2), reason=f"Average ICD code confidence ({len(diagnoses)} codes)"
            )

        # --- Medications ---
        med_matches = re.finditer(MEDICATION_PATTERN, text)
        for match in med_matches:
            name = match.group(1).strip()
            dose = match.group(2).strip()
            freq = match.group(3).strip()
            medications.append(MedicationModel(
                name=name, dose=dose, frequency=freq, confidence=0.6
            ))

        if medications:
            field_confidence["medications"] = FieldConfidence(
                value=0.6, reason="Regex medication pattern match (no full context verification)"
            )

        # --- Compute overall confidence ---
        weights = {
            "patient.name": 0.2,
            "patient.birth_date": 0.15,
            "diagnoses": 0.25,
            "medications": 0.2,
            "vitals.bp": 0.1,
            "vitals.spo2": 0.05,
            "vitals.hr": 0.05,
        }

        total_weight = 0.0
        weighted_sum = 0.0
        for field, weight in weights.items():
            if field in field_confidence:
                weighted_sum += field_confidence[field].value * weight
                total_weight += weight

        overall_confidence = round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0

        # Penalize if missing critical fields
        if not diagnoses:
            overall_confidence = max(0.0, overall_confidence - 0.1)
        # Regex fallback is inherently less reliable
        overall_confidence = round(overall_confidence * 0.8, 2)

        return ExtractionResponse(
            patient=patient,
            vitals=vitals,
            diagnoses=diagnoses,
            medications=medications,
            dates=dates,
            extraction_method="regex_fallback",
            confidence=overall_confidence,
            field_confidence=field_confidence,
        )
