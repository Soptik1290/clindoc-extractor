class ClinDocException(Exception):
    """Base exception for ClinDoc Extractor."""
    pass

class ExtractionError(ClinDocException):
    """Raised when extraction fails completely."""
    pass
