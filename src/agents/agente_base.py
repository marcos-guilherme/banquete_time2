from abc import ABC, abstractmethod


class AgenteBase(ABC):
    """Interface Base para todos os Agentes"""
    @abstractmethod
    def Analisar(self, texto: str):
        pass