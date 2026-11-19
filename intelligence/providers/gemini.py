import os

from dotenv import load_dotenv
from google import genai

from intelligence.providers.base import ProvedorIA

# Carrega as variáveis do arquivo .env na raiz do projeto
load_dotenv()


class GeminiProvider(ProvedorIA):
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.modelo = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

        self.client = None

        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)

    def verificar_conexao(self) -> bool:
        return self.client is not None

    def gerar_texto(self, prompt: str) -> str:
        if not self.client:
            raise RuntimeError("GEMINI_API_KEY não encontrada no arquivo .env.")

        resposta = self.client.models.generate_content(
            model=self.modelo, contents=prompt
        )

        if not resposta.text:
            raise RuntimeError("O Gemini não retornou conteúdo textual.")

        return resposta.text.strip()
