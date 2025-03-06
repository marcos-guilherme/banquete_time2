from prefect import flow, task
from src.agents.agent_factory import AgentFactory
from schemas.modelos_base import InputData

@task
def run_extracaoProcedimentos(data: dict):
    try:
        input_data = InputData(**data)  # Validando o dicionário com o modelo Pydantic
        input_data = input_data.model_dump()  # Convertendo para dicionário
        agente = AgentFactory.obter_agente("extracao_procedimentos")()
        resultado = agente.Analisar(input_data['text'])  # Passando 'text' do modelo Pydantic
        return resultado
    except ValueError as e:
        return {"error": str(e)}

@task
def run_decodificacao(data: dict):
    agente = AgentFactory.obter_agente("fazer_decodificacao")
    resultado = agente.Analisar(data["text"])
    return resultado.dict()

@task
def obter_tabela(data: dict):
    pass

@task
def format_to_xml(data: dict):
    pass

@flow(name="fluxo_principal")
def fluxo_principal(data: dict):
    extracao = run_extracaoProcedimentos(data)
    resultado_tabela = obter_tabela(extracao)
    resultado_xml = format_to_xml(resultado_tabela)
    decodificacao = run_decodificacao(resultado_xml)
    return decodificacao.dict()