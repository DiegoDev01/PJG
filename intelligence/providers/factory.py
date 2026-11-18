import os

from intelligence.providers.gemini import GeminiProvider
from intelligence.providers.ollama import OllamaProvider


def criar_provedor():
    provedor = os.getenv("IA_PROVIDER", "gemini").lower().strip()

    if provedor == "gemini":
        return GeminiProvider()

    if provedor == "ollama":
        return OllamaProvider()

    raise ValueError(
        f"Provedor de IA não reconhecido: {provedor}"
    )