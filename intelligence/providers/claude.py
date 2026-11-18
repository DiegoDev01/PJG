import os

from intelligence.providers.base import ProvedorIA


class ClaudeProvider(ProvedorIA):

    def verificar_conexao(self) -> bool:
        return bool(os.getenv("ANTHROPIC_API_KEY"))

    def gerar_texto(self, prompt: str) -> str:
        if not self.verificar_conexao():
            raise RuntimeError("Chave da API do Claude não configurada.")

        try:
            import anthropic
        except ImportError:
            raise RuntimeError(
                "Instale a biblioteca anthropic para utilizar o Claude."
            )

        cliente = anthropic.Anthropic()

        resposta = cliente.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return resposta.content[0].text