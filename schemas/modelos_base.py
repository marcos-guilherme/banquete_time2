from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from schemas.modelos_para_agentes import Procedimento

class InputData(BaseModel):
    """Modelo para dados de entrada da API."""
    text: str = Field(..., description="Texto a ser processado")
    model_name: Optional[str] = Field(default="gpt-4o-mini", description="Nome do modelo a ser usado")
    temperature: Optional[float] = Field(default=0.1, description="Temperatura para geração de texto")
    
# Definir um modelo para a entrada da verificação
class VerificacaoInput(BaseModel):
    """Modelo para dados de entrada da verificação."""
    text: str  # O texto original (mesmo input do extrator)
    procedimentos_identificados: Optional[List[Procedimento]] = None  # Saída do extrator
    

class DecodificacaoInput(BaseModel):
    """Modelo para dados de entrada da decodificação."""
    procedimentos_verificados: List[Dict[str, Any]] = Field(..., description="Lista de procedimentos verificados")
    documentos_similares: Optional[List[Dict[str, Any]]] = Field(None, description="Lista de documentos similares (opcional)")
    
class BuscaDocumentosInput(BaseModel):
    """Modelo para dados de entrada da busca de documentos similares."""
    procedimentos_verificados: List[Dict[str, Any]]
    match_count: Optional[int] = 15
    
class InputDataComLaudo(BaseModel):
    """Modelo para dados de entrada com descrição cirúrgica e laudo anatomopatológico."""
    text: str = Field(..., description="Texto da descrição cirúrgica")
    laudo: Optional[str] = Field(None, description="Texto do laudo anatomopatológico")