# banquete_time2

## Lista de Pacotes pip para o Projeto

Este documento contém a lista de pacotes `pip` necessários para o projeto.


### Pacotes (Por enquanto)

 - pip install pydantic
 - pip install langchain
 - pip install python-dotenv (por precaução)

## Construção de Agentes
 - **Agente Base:** Define o que deve ser implementado para incorporarmos um agente.

 - **Agent Factory:** A 'Fábrica' de agentes contém um dicionário que diz para ela, a partir de uma string que agente deve ser criado.

 - **Info:** Para criar um novo agente basta em agentes.py criar a classe que herda o Agente Base e definir seu método abstrato Analisar(). E por fim adicioná-lo ao Agent Factory para que ele possa finalmente ser 'fabricado'.


### Não esqueça de adicionar as variáveis de ambiente num arquivo .env

#### Exemplo de uso:
 ```python
from agentes.agent_factory import AgentFactory

agente_procedimentos = AgentFactory.obter_agente("extracao_procedimentos")()
resultado_procedimentos = agente_procedimentos.Analisar(texto) 
```

#### .....