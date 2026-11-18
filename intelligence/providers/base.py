from abc import ABC, abstractmethod


class ProvedorIA(ABC):

    @abstractmethod
    def gerar_texto(self, prompt: str) -> str:
        """Gera texto usando o provedor de IA."""
        pass

    @abstractmethod
    def verificar_conexao(self) -> bool:
        """Verifica se o provedor está disponível."""
        pass