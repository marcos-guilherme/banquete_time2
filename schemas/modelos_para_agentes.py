from typing import Optional, List
from pydantic import BaseModel, Field

class Procedimento(BaseModel):
    """Modelo básico para um procedimento médico."""
    procedimento: str = Field(description="Nome do procedimento identificado.")
    descricao: str = Field(description=None)

class ProcedimentoExtracao(BaseModel):
    """Modelo ajustado para garantir que a extração sempre retorne uma lista de procedimentos."""
    procedimentos_identificados: List[Procedimento] = Field(description="Lista de procedimentos extraídos do texto.")

    

class Decodificacao(BaseModel):
    """Modelo ajustado para garantir que a decodificação funcione diretamente com uma lista."""
    nome_procedimentos: Procedimento = Field(description="Nome do procedimento decodificado. (O que tem a maior evidência dado os documentos)")
    codigo_procedimentos: str = Field(description="O código do procedimento que foi identificado.")
    tratar_cancer: bool = Field(description="Indica se cada procedimento tem como objetivo tratar o câncer atual do paciente")
    

class IdentificacaoPecaAnatomica(BaseModel):
    """Modelo simplificado para identificação de retirada de peça anatômica."""
    retirada_peca_anatomica: bool = Field(description="Indica se houve retirada de peça anatômica do paciente.")
    justificativa: str = Field(description="Justificativa para a conclusão, citando trechos relevantes do texto.")
    
class ProcedimentoLaudoAnatomopatologico(BaseModel):
    """Modelo para procedimentos extraídos de laudos anatomopatológicos."""
    procedimento: str = Field(description="Nome do procedimento identificado no laudo.")
    descricao: str = Field(description="Descrição do procedimento conforme o laudo.")
    peca_anatomica: str = Field(description="Descrição da peça anatômica analisada.")

class ExtratorLaudoAnatomopatologico(BaseModel):
    """Modelo para a extração de informações de laudos anatomopatológicos."""
    procedimentos_laudo: List[ProcedimentoLaudoAnatomopatologico] = Field(
        description="Lista de procedimentos extraídos do laudo anatomopatológico."
    )
    
class VerificacaoTrauma(BaseModel):
    """Modelo para verificação de entrada por trauma/acidente."""
    entrada_por_trauma: bool = Field(description="Indica se o paciente deu entrada por trauma/acidente")
    justificativa: str = Field(description="Justificativa para a conclusão sobre entrada por trauma/acidente")
    

class VerificacaoMesmaDoenca(BaseModel):
    """Modelo para verificação se os procedimentos são para tratar a mesma doença."""
    mesma_doenca: bool = Field(description="Indica se os procedimentos são para tratar a mesma doença")
    justificativa: str = Field(description="Justificativa para a conclusão sobre mesma doença")