import logging
from openai import AsyncOpenAI
from app.extraction.base import BaseExtractor
from app.models.response import ExtractionResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a clinical NLP expert specializing in Central European medical documentation.
Extract structured clinical data from the provided medical dictation.

The text may be in Czech, English, or mixed (including Latin medical terms and abbreviations).

Rules:
- patient.birth_date: always return in ISO 8601 format (YYYY-MM-DD)
- dates.admission: always return in ISO 8601 format (YYYY-MM-DD)
- vitals.bp: return as "systolic/diastolic" (e.g., "178/95")
- vitals.spo2: return numeric value with % (e.g., "97%")
- vitals.hr: include units (e.g., "92 bpm")
- diagnoses: extract ALL ICD codes found, system is always "ICD-10"
- medications: extract name, dose, frequency for each drug mentioned
- follow_up: extract recommended follow-up instructions if mentioned
- If a field cannot be reliably extracted, omit it (do not guess)
- For confidence scoring: assign 0.0-1.0 per field based on text clarity and reasons. Populate the field_confidence mapping (keys: patient.name, patient.birth_date, etc.). Also provide an overall confidence score between 0.0 and 1.0.

Respond ONLY with valid JSON matching the provided schema.
"""

class LLMExtractor(BaseExtractor):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        
    async def extract(self, text: str, language: str = "auto") -> ExtractionResponse | None:
        try:
            response = await self.client.beta.chat.completions.parse(
                model=settings.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Language hint: {language}\n\nText:\n{text}"}
                ],
                response_format=ExtractionResponse,
                timeout=settings.openai_timeout,
            )
            parsed = response.choices[0].message.parsed
            if parsed:
                parsed.extraction_method = "llm"
            return parsed
        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}")
            return None
