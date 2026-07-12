import logging
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    """
    Returns a singleton OpenAI client.
    Initialised lazily so tests that do not use AI features
    do not require a valid API key.
    """
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client
