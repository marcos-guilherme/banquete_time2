from typing import Optional, List

from pydantic import BaseModel, Field


class Procedimento(BaseModel):
    """Informação sobre procedimentos médicos."""
    
    name: Optional[str] = Field(default=None,
                                description="Nome do procedimento médico ao qual o paciente será submetido. Exemplo: 'Ressonância Magnética', 'Tomografia Computadorizada', 'Cirurgia Cardíaca'.")
    
    
class ProcedimentosExtraidos(BaseModel):
    """Lista de procedimentos médicos extraídos de um texto."""
    
    procedimentos: List[Procedimento]
    
    
class VerificacaoOncologica(BaseModel):
    """Avaliação sobre possível condição oncológica."""
    
    e_oncologico: Optional[bool] = Field(
        default=False,
        description="Indica se há evidências no texto de que o paciente tem câncer ou está sob investigação oncológica."
    )