from loguru import logger
from typing import Dict, Any, Callable, List, Optional

class DecisorFluxo:
    """
    Classe para decidir qual fluxo seguir com base nos resultados dos agentes.
    """
    
    def __init__(self):
        """Inicializa o decisor de fluxo."""
        # Dicionário de fluxos disponíveis
        self.fluxos = {}
        
    def registrar_fluxo(self, nome_fluxo: str, funcao_fluxo: Callable, condicao: Callable = None):
        """
        Registra um fluxo com sua função e condição de ativação.
        
        Args:
            nome_fluxo: Nome do fluxo
            funcao_fluxo: Função a ser executada para este fluxo
            condicao: Função que recebe os resultados e retorna True se o fluxo deve ser ativado
        """
        self.fluxos[nome_fluxo] = {
            "funcao": funcao_fluxo,
            "condicao": condicao
        }
        logger.info(f"Fluxo '{nome_fluxo}' registrado")
        
    def decidir_fluxo(self, resultados: Dict[str, Any], fluxo_padrao: str = None) -> str:
        """
        Decide qual fluxo seguir com base nos resultados dos agentes.
        
        Args:
            resultados: Dicionário com os resultados dos agentes
            fluxo_padrao: Nome do fluxo padrão a ser seguido se nenhuma condição for atendida
            
        Returns:
            Nome do fluxo a ser seguido
        """
        logger.info("Decidindo qual fluxo seguir")
        
        # Verificar cada fluxo registrado
        for nome_fluxo, config in self.fluxos.items():
            # Se não há condição, pular
            if config["condicao"] is None:
                continue
                
            # Verificar se a condição é atendida
            try:
                if config["condicao"](resultados):
                    logger.info(f"Condição atendida para o fluxo '{nome_fluxo}'")
                    return nome_fluxo
            except Exception as e:
                logger.error(f"Erro ao verificar condição para o fluxo '{nome_fluxo}': {str(e)}")
        
        # Se nenhuma condição foi atendida, retornar o fluxo padrão
        if fluxo_padrao and fluxo_padrao in self.fluxos:
            logger.info(f"Nenhuma condição atendida, seguindo fluxo padrão '{fluxo_padrao}'")
            return fluxo_padrao
        
        # Se não há fluxo padrão ou ele não existe, retornar None
        logger.warning("Nenhum fluxo foi selecionado")
        return None
    
    def executar_fluxo(self, nome_fluxo: str, *args, **kwargs):
        """
        Executa o fluxo especificado.
        
        Args:
            nome_fluxo: Nome do fluxo a ser executado
            *args, **kwargs: Argumentos a serem passados para a função do fluxo
            
        Returns:
            Resultado da execução do fluxo
        """
        if nome_fluxo not in self.fluxos:
            logger.error(f"Fluxo '{nome_fluxo}' não encontrado")
            return None
            
        logger.info(f"Executando fluxo '{nome_fluxo}'")
        try:
            return self.fluxos[nome_fluxo]["funcao"](*args, **kwargs)
        except Exception as e:
            logger.error(f"Erro ao executar fluxo '{nome_fluxo}': {str(e)}")
            return None
    
    def decidir_e_executar(self, resultados: Dict[str, Any], fluxo_padrao: str = None, *args, **kwargs):
        """
        Decide qual fluxo seguir e o executa.
        
        Args:
            resultados: Dicionário com os resultados dos agentes
            fluxo_padrao: Nome do fluxo padrão a ser seguido se nenhuma condição for atendida
            *args, **kwargs: Argumentos a serem passados para a função do fluxo
            
        Returns:
            Resultado da execução do fluxo
        """
        nome_fluxo = self.decidir_fluxo(resultados, fluxo_padrao)
        if nome_fluxo:
            return self.executar_fluxo(nome_fluxo, *args, **kwargs)
        return None