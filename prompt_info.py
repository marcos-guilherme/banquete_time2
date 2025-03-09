from langchain_core.prompts import ChatPromptTemplate
from functions import load_prompt

#Defina aqui os templates de todos os agentes que rpecisar, para depois carregá-lo em agentes.py

prompt_template_procedimentos = ChatPromptTemplate.from_messages([
    ("system", load_prompt(r"prompts\system_extracao_procedimentos.txt")),
    
    ("human", "{text}")
])

prompt_decodificacao = ChatPromptTemplate.from_messages([
    ("system", load_prompt(r"prompts\system_decodificacao.txt")),
    ("human", "{text}")
])

