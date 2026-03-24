import logging
from app.extraction.pipeline import ExtractionPipeline
from app.models.response import ExtractionResponse
from app.utils.language_detector import detect_language

logger = logging.getLogger(__name__)


class ExtractorService:
    """Business logic layer for clinical data extraction.

    Wraps the extraction pipeline and provides a clean interface
    for API routes and other consumers.
    """

    def __init__(self) -> None:
        self.pipeline = ExtractionPipeline()

    async def extract(self, text: str, language: str = "auto") -> ExtractionResponse:
        """Run full extraction pipeline on the given text.

        Args:
            text: Raw medical dictation text.
            language: Language hint — "cs", "en", or "auto".

        Returns:
            ExtractionResponse with structured clinical data.
        """
        if language == "auto":
            detected = detect_language(text)
            logger.info(f"Auto-detected language: {detected}")
            language = detected

        return await self.pipeline.process(text, language)
