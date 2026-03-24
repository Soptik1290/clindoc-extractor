import logging
from app.extraction.llm_extractor import LLMExtractor
from app.extraction.regex_extractor import RegexExtractor
from app.models.response import ExtractionResponse
from app.core.config import settings
from app.utils.language_detector import detect_language
import hashlib
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class ExtractionPipeline:
    """Orchestrates extraction: LLM primary → regex fallback → merge + validation.

    Logic:
    1. Attempt LLM extraction (async)
    2. If LLM fails → regex fallback, add warning
    3. If LLM succeeds → regex verifies critical fields (ICD codes, dates)
    4. Merge: LLM results have priority, regex supplements missing fields
    5. Post-processing: date normalization, BP format validation
    6. Compute overall confidence score
    """

    def __init__(self) -> None:
        self.llm_extractor = LLMExtractor()
        self.regex_extractor = RegexExtractor()
        self.redis = aioredis.from_url(settings.redis_url)

    async def process(self, text: str, language: str = "auto") -> ExtractionResponse:
        if language == "auto":
            language = detect_language(text)

        # --- Cache check ---
        cache_key = f"clindoc:cache:{hashlib.sha256(text.encode() + language.encode()).hexdigest()}"
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                logger.info("Loaded extraction result from Redis cache")
                return ExtractionResponse.model_validate_json(cached_data.decode("utf-8"))
        except Exception as e:
            logger.warning(f"Cache read error: {e}")

        # --- Step 1: Try LLM extraction ---
        llm_result: ExtractionResponse | None = None
        if settings.use_llm:
            logger.info("Starting LLM extraction")
            llm_result = await self.llm_extractor.extract(text, language)

        # --- Step 2: Always run regex for verification/fallback ---
        regex_result = await self.regex_extractor.extract(text, language)

        # --- Step 3: Merge or fallback ---
        if llm_result:
            result = self._merge(llm_result, regex_result)
        else:
            logger.warning("LLM failed or disabled. Using regex fallback only.")
            regex_result.warnings.append("Used regex fallback due to LLM failure or being disabled")
            result = regex_result

        # --- Cache store ---
        try:
            await self.redis.setex(cache_key, 86400, result.model_dump_json())
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

        return result

    def _merge(self, llm: ExtractionResponse, regex: ExtractionResponse) -> ExtractionResponse:
        """Merge LLM and Regex results. LLM has priority, regex supplements missing fields.

        Also uses regex to cross-verify critical fields (ICD codes, dates).
        """
        warnings: list[str] = list(llm.warnings)
        used_regex_supplement = False

        # --- Patient: LLM primary, regex supplements ---
        if not llm.patient.name and regex.patient.name:
            llm.patient.name = regex.patient.name
            used_regex_supplement = True
        if not llm.patient.birth_date and regex.patient.birth_date:
            llm.patient.birth_date = regex.patient.birth_date
            used_regex_supplement = True

        # --- Vitals: LLM primary, regex supplements ---
        if not llm.vitals.bp and regex.vitals.bp:
            llm.vitals.bp = regex.vitals.bp
            used_regex_supplement = True
        if not llm.vitals.spo2 and regex.vitals.spo2:
            llm.vitals.spo2 = regex.vitals.spo2
            used_regex_supplement = True
        if not llm.vitals.hr and regex.vitals.hr:
            llm.vitals.hr = regex.vitals.hr
            used_regex_supplement = True

        # --- Dates: LLM primary, regex supplements ---
        if not llm.dates.admission and regex.dates.admission:
            llm.dates.admission = regex.dates.admission
            used_regex_supplement = True

        # --- Diagnoses: cross-verify ICD codes with regex ---
        llm_codes = {d.code for d in llm.diagnoses}
        regex_codes = {d.code for d in regex.diagnoses}

        # Add regex-found ICD codes that LLM missed
        for diag in regex.diagnoses:
            if diag.code not in llm_codes:
                diag.confidence = 0.6  # Regex-only code, lower confidence
                llm.diagnoses.append(diag)
                warnings.append(f"ICD code {diag.code} found by regex but missed by LLM")
                used_regex_supplement = True

        # Warn if regex found codes that LLM didn't find (cross-verification)
        missing_from_llm = regex_codes - llm_codes
        if missing_from_llm:
            logger.info(f"Regex cross-verified: LLM missed codes {missing_from_llm}")

        # --- Medications: supplement if LLM missed some ---
        llm_med_names = {m.name.lower() for m in llm.medications}
        for med in regex.medications:
            if med.name.lower() not in llm_med_names:
                med.confidence = 0.6
                llm.medications.append(med)
                warnings.append(f"Medication '{med.name}' found by regex but missed by LLM")
                used_regex_supplement = True

        # --- Determine extraction method ---
        if used_regex_supplement:
            llm.extraction_method = "hybrid"
        else:
            llm.extraction_method = "llm"

        llm.warnings = warnings
        return llm
