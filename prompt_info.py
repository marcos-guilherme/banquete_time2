from langchain_core.prompts import ChatPromptTemplate
from functions import load_prompt

#Defina aqui os templates de todos os agentes que rpecisar, para depois carregá-lo em agentes.py

prompt_template_procedimentos = ChatPromptTemplate.from_messages([
    ("system", load_prompt(r"prompts\system_procedures_extraction.txt")),
    
    ("human", "{text}")
])

