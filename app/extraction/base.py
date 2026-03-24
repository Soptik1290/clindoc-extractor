from abc import ABC, abstractmethod
from app.models.response import ExtractionResponse


class BaseExtractor(ABC):
    """Abstract base class for all clinical data extractors."""

    @abstractmethod
    async def extract(self, text: str, language: str = "auto") -> ExtractionResponse | None:
        """Extract structured clinical data from raw medical text.

        Args:
            text: The raw medical dictation or report text.
            language: Language hint — "cs", "en", or "auto" for auto-detection.

        Returns:
            ExtractionResponse with extracted data, or None if extraction fails.
        """
        ...
