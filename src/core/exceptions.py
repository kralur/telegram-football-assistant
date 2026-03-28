class ExternalAPIError(Exception):
    """Raised when external API fails."""
    pass


class AIServiceError(Exception):
    """Raised when AI service fails."""
    pass