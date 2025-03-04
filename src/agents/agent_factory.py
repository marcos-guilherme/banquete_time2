from .agentes import extracaoProcedimentos

class AgentFactory:
    
    """Sempre que cinstruirmos um agente em agentes.py, devemos definir a string a que se refere este agente, como pares chave-valor no dicionário agentes.
       A partir disso, podemos obter o agente correspondente a partir de uma string que o identifica.
    """
    
    @staticmethod
    def obter_agente(tipo_agente: str):
        agentes = {
            "extracao_procedimentos": extracaoProcedimentos,
            "StringParaObterAgente": "FunçãoDoAgente"
        }
        
        if tipo_agente not in agentes:
            raise ValueError(f"Tipo de agente desconhecido: {tipo_agente}")
        
        return agentes[tipo_agente]