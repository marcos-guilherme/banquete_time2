from src.flows.config_fluxos import configurar_decisor_fluxo
from src.flows.fluxo_chain import (
    executar_chain_extracao,
    executar_chain_identificacao_peca,
    executar_verificacao_trauma,
    executar_verificacao_mesma_doenca
)
from loguru import logger

def processar_texto_e_decidir_fluxo(texto, laudo_anatomopatologico=None):
    """
    Processa o texto, executa os agentes necessários para a decisão e decide qual fluxo seguir.
    
    Args:
        texto: Texto da descrição cirúrgica a ser processado
        laudo_anatomopatologico: Texto do laudo anatomopatológico (opcional)
        
    Returns:
        Resultado do fluxo selecionado
    """
    logger.info("Processando texto e decidindo fluxo")
    
    # Configurar o decisor de fluxo
    decisor = configurar_decisor_fluxo()
    
    # Verificar primeiro se o laudo foi fornecido
    if not laudo_anatomopatologico:
        logger.info("Laudo anatomopatológico não fornecido, usando fluxo sem peça anatômica")
        try:
            # Executar diretamente o fluxo sem peça anatômica
            resultado = decisor.fluxos["fluxo_sem_peca_anatomica"]["funcao"](texto)
            return resultado
        except Exception as e:
            logger.error(f"Erro ao executar fluxo sem peça anatômica: {str(e)}")
            # Tentar um fluxo mais simples em caso de erro
            return executar_fluxo_simplificado(texto)
    
    # Se chegou aqui, é porque o laudo foi fornecido
    # Agora verificamos se há retirada de peça anatômica
    resultados = {}
    
    try:
        resultado_peca = executar_chain_identificacao_peca(texto)
        resultados["retirada_peca_anatomica"] = resultado_peca.retirada_peca_anatomica
        resultados["justificativa_peca"] = resultado_peca.justificativa
        logger.info(f"Retirada de peça anatômica: {resultados['retirada_peca_anatomica']}")
        
        # Se foi identificada peça anatômica, usar o fluxo com peça anatômica
        if resultados["retirada_peca_anatomica"]:
            logger.info("Peça anatômica identificada, usando fluxo com peça anatômica")
            try:
                resultado = decisor.fluxos["fluxo_com_peca_anatomica"]["funcao"](texto, laudo_anatomopatologico)
                return resultado
            except Exception as e:
                logger.error(f"Erro ao executar fluxo com peça anatômica: {str(e)}")
                # Tentar um fluxo mais simples em caso de erro
                return executar_fluxo_simplificado(texto)
        else:
            logger.info("Peça anatômica não identificada, usando fluxo sem peça anatômica")
            try:
                resultado = decisor.fluxos["fluxo_sem_peca_anatomica"]["funcao"](texto)
                return resultado
            except Exception as e:
                logger.error(f"Erro ao executar fluxo sem peça anatômica: {str(e)}")
                # Tentar um fluxo mais simples em caso de erro
                return executar_fluxo_simplificado(texto)
            
    except Exception as e:
        logger.error(f"Erro ao identificar peça anatômica: {str(e)}")
        # Em caso de erro na identificação, usar o fluxo sem peça anatômica por segurança
        logger.info("Usando fluxo sem peça anatômica devido a erro na identificação")
        try:
            resultado = decisor.fluxos["fluxo_sem_peca_anatomica"]["funcao"](texto)
            return resultado
        except Exception as e:
            logger.error(f"Erro ao executar fluxo sem peça anatômica após erro na identificação: {str(e)}")
            # Tentar um fluxo mais simples em caso de erro
            return executar_fluxo_simplificado(texto)
        
def executar_fluxo_simplificado(texto):
    """
    Executa um fluxo simplificado em caso de erro nos fluxos principais.
    Este fluxo faz apenas a extração e classificação básica.
    
    Args:
        texto: Texto da descrição cirúrgica
        
    Returns:
        Resultado simplificado
    """
    logger.info("Executando fluxo simplificado devido a erros anteriores")
    
    try:
        # Extrair procedimentos
        resultado_extracao = executar_chain_extracao(texto)
        
        # Verificar entrada por trauma diretamente
        entrada_por_trauma = executar_verificacao_trauma(texto)
        
        # Verificar se os procedimentos são para a mesma doença
        mesma_doenca = executar_verificacao_mesma_doenca(resultado_extracao.procedimentos_identificados)
        
        # Verificar se há mais de um procedimento
        multiplos_procedimentos = len(resultado_extracao.procedimentos_identificados) > 1
        
        # Determinar classificação
        classificacao_final = ""
        if entrada_por_trauma and multiplos_procedimentos:
            classificacao_final = "politrauma"
        elif not entrada_por_trauma and multiplos_procedimentos:
            if mesma_doenca:
                classificacao_final = "sequencial"
            else:
                classificacao_final = "multipla"
        else:
            classificacao_final = "procedimento_isolado"
        
        # Construir resultado
        return {
            "extracao": resultado_extracao,
            "classificacao_final": classificacao_final,
            "detalhes_classificacao": {
                "entrada_por_trauma": entrada_por_trauma,
                "multiplos_procedimentos": multiplos_procedimentos,
                "mesma_doenca": mesma_doenca,
                "numero_procedimentos": len(resultado_extracao.procedimentos_identificados)
            },
            "tipo_fluxo": "simplificado"
        }
    except Exception as e:
        logger.error(f"Erro no fluxo simplificado: {str(e)}")
        # Retornar um resultado mínimo em caso de erro
        return {
            "erro": str(e),
            "classificacao_final": "não_classificado",
            "tipo_fluxo": "erro"
        }