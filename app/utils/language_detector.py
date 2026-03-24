from langdetect import detect, DetectorFactory
from typing import Literal

# To ensure deterministic results
DetectorFactory.seed = 0

def detect_language(text: str) -> Literal["cs", "en", "auto"]:
    """Detects if text is primarily English or Czech."""
    try:
        lang = detect(text)
        if lang == "cs":
            return "cs"
        elif lang == "en":
            return "en"
        return "auto"
    except Exception:
        return "auto"
