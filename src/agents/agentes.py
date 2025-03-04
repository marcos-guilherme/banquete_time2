from .agente_base import AgenteBase
from langchain.chat_models import init_chat_model
from prompt_info import prompt_template_procedimentos
from schemas import ProcedimentosExtraidos

"""
Aqui os agentes devem ser implementados. Cada agente deve herdar da classe AgenteBase e implementar o método Analisar.
Permite definirmos a logica de cada agente de forma isolada, facilitando a manutenção e a evolução do sistema.
"""


class extracaoProcedimentos(AgenteBase):
    """Executar ação de extração de procedimentos"""
    def __init__(self):
        self.llm = init_chat_model("gpt-4-turbo", model_provider="openai")
        
    def Analisar(self, texto):
        self.prompt = prompt_template_procedimentos.invoke({"text": texto}) #Extrair o template (system prompt) para o caso específico. (Podem ser definidos em prompt info).
        self.structured_llm = self.llm.with_structured_output(schema=ProcedimentosExtraidos) #Não esqueça de criar um "esquema" em schemas.py e adicionsá-lo aqui.
        return self.structured_llm.invoke(self.prompt)
    
class JamesBond(AgenteBase):
    """Agente secreto"""
    def __init__(self):
        pass
    def Analisar(self, texto):
        return "James Bond"