from pydantic import BaseModel
from typing import Optional, List

class OutputProcedimentos(BaseModel):
    codigo: str
    descricao: str
    
class OutputProcedimentosExtraidos(BaseModel):
    procedimentos: List[OutputProcedimentos]  
