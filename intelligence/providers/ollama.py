import requests

from intelligence.providers.base import ProvedorIA


class OllamaProvider(ProvedorIA):

    def __init__(self, modelo="qwen2.5:7b"):
        self.modelo = modelo
        self.url = "http://localhost:11434/api/generate"

    def verificar_conexao(self) -> bool:
        try:
            resposta = requests.get(
                "http://localhost:11434/api/tags",
                timeout=5
            )
            resposta.raise_for_status()

            modelos = resposta.json().get("models", [])

            return any(
                modelo["name"] == self.modelo
                for modelo in modelos
            )

        except requests.RequestException:
            return False

    def gerar_texto(self, prompt: str) -> str:
        resposta = requests.post(
            self.url,
            json={
                "model": self.modelo,
                "prompt": prompt,
                "stream": False
            },
            timeout=300
        )

        resposta.raise_for_status()

        return resposta.json()["response"].strip()