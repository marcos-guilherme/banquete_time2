from .agente_base import AgenteBase
from langchain.chat_models import init_chat_model
from prompt_info import prompt_template_procedimentos, prompt_decodificacao
from schemas.modelos_para_agentes import ResumoProcedimento, decodificacao
from langchain_openai import ChatOpenAI
import dotenv
import os

dotenv.load_dotenv()
open_ai_key = os.getenv("OPENAI_API_KEY")


"""
Aqui os agentes devem ser implementados. Cada agente deve herdar da classe AgenteBase e implementar o método Analisar.
Permite definirmos a logica de cada agente de forma isolada, facilitando a manutenção e a evolução do sistema.
"""


class extracaoProcedimentos(AgenteBase):
    """Executar ação de extração de procedimentos"""
    def __init__(self):
        self.llm = ChatOpenAI(openai_api_key=open_ai_key, model="gpt-4o-mini")
        
    def Analisar(self, text):
        self.prompt = prompt_template_procedimentos.invoke({'text': text}) #Extrair o template (system prompt) para o caso específico. (Podem ser definidos em prompt info).
        self.structured_llm = self.llm.with_structured_output(schema=ResumoProcedimento)
        self.resultado = self.structured_llm.invoke(self.prompt)
        
        return self.resultado.model_dump()



class decodificacao(AgenteBase):
    def __init__(self):
        self.llm = ChatOpenAI(openai_api_key=open_ai_key, model="gpt-4o-mini")
        
    def Analisar(self, text):
        self.prompt = prompt_decodificacao.invoke({"text": text}) #Extrair o template (system prompt) para o caso específico. (Podem ser definidos em prompt info).
        structured_llm = self.llm.with_structured_output(schema=decodificacao)
        self.resultado = structured_llm.invoke(self.prompt)
        
        return self.resultado.model_dump()
        
