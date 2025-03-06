from typing import Optional, List

from pydantic import BaseModel, Field


class Procedimento(BaseModel):
    """Informação sobre procedimentos médicos."""
    
    name: Optional[str] = Field(default=None, description="Um procedimento é uma sequência estruturada de ações realizadas para alcançar um objetivo específico. No contexto cirúrgico, refere-se a uma intervenção médica que segue etapas definidas, como diérese, hemostasia, exérese e síntese, podendo envolver a remoção, reparação ou modificação de tecidos ou órgãos. A inclusão de procedimentos adicionais só ocorre quando suas etapas não estão contempladas em outro procedimento já realizado.")
    
    
class ProcedimentosExtraidos(BaseModel):
    """Lista de procedimentos médicos extraídos de um texto."""
    
    procedimentos: List[Procedimento]
    
class Indicio(BaseModel):
    """Representa um indício encontrado no texto que reforça a identificação do procedimento."""
    descricao: str
    
class ResumoProcedimento(BaseModel):
    """Estrutura final para consolidar os procedimentos e indícios extraídos."""
    #nome_procedimento: Optional[str] = Field(default=None, description="Nome principal do procedimento identificado")
    procedimentos_identificados: List[Procedimento] = Field(description="Lista de procedimentos realizados")
    indicios: List[Indicio] = Field(description="Lista de indícios encontrados no texto")
    
class decodificacao(BaseModel):
    pass
    