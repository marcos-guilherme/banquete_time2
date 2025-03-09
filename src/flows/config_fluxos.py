from src.flows.decisor_fluxo import DecisorFluxo
from src.flows.fluxo_chain import (
    executar_chain_completa,
    executar_chain_extracao,
    executar_chain_decodificacao,
    executar_extracao_laudo,
    executar_busca_documentos,
    executar_comparacao_procedimentos,
    executar_verificacao_trauma,
    executar_verificacao_mesma_doenca
)
from loguru import logger

def configurar_decisor_fluxo():
    """
    Configura o decisor de fluxo com os fluxos disponíveis e suas condições.
    
    Returns:
        DecisorFluxo configurado
    """
    decisor = DecisorFluxo()
    
    # Registrar fluxos
    
    # Fluxo completo (padrão)
    decisor.registrar_fluxo(
        "fluxo_completo",
        executar_chain_completa
    )
    
    # Fluxo para casos com retirada de peça anatômica
    decisor.registrar_fluxo(
        "fluxo_com_peca_anatomica",
        fluxo_com_peca_anatomica,
        lambda resultados: resultados.get("retirada_peca_anatomica") is True
    )
    
    # Fluxo para casos sem retirada de peça anatômica
    decisor.registrar_fluxo(
        "fluxo_sem_peca_anatomica",
        fluxo_sem_peca_anatomica,
        lambda resultados: resultados.get("retirada_peca_anatomica") is False
    )
    
    decisor.registrar_fluxo(
        "fluxo_classificacao_final",
        fluxo_classificacao_final,
        lambda resultados: "decodificacao" in resultados
    )
    
    # Removido: Fluxo para casos de tratamento de câncer
    # decisor.registrar_fluxo(
    #     "fluxo_tratamento_cancer",
    #     fluxo_tratamento_cancer,
    #     lambda resultados: any(
    #         tratar_cancer for tratar_cancer in resultados.get("decodificacao", {}).get("tratar_cancer", [False])
    #     )
    # )
    
    # Removido: Fluxo para casos sem tratamento de câncer
    # decisor.registrar_fluxo(
    #     "fluxo_sem_tratamento_cancer",
    #     fluxo_sem_tratamento_cancer,
    #     lambda resultados: not any(
    #         tratar_cancer for tratar_cancer in resultados.get("decodificacao", {}).get("tratar_cancer", [False])
    #     )
    # )
    
    # Removido: Fluxo combinado: com peça anatômica E tratamento de câncer
    # decisor.registrar_fluxo(
    #     "fluxo_peca_e_cancer",
    #     fluxo_peca_e_cancer,
    #     lambda resultados: (
    #         resultados.get("retirada_peca_anatomica") is True and
    #         any(tratar_cancer for tratar_cancer in resultados.get("decodificacao", {}).get("tratar_cancer", [False]))
    #     )
    # )
    
    return decisor

# Implementação dos fluxos específicos

def fluxo_com_peca_anatomica(texto, laudo_anatomopatologico=None):
    """
    Fluxo para casos com retirada de peça anatômica.
    
    Este fluxo executa um processo especializado que:
    1. Extrai procedimentos da descrição cirúrgica
    2. Se disponível, extrai procedimentos do laudo anatomopatológico
    3. Compara e corrige os procedimentos com base nas duas fontes e no vector storage
    4. Decodifica os procedimentos corrigidos
    
    Args:
        texto: Descrição cirúrgica
        laudo_anatomopatologico: Laudo anatomopatológico (opcional)
        
    Returns:
        Resultado do processamento com procedimentos corrigidos
    """
    logger.info("Executando fluxo para casos com retirada de peça anatômica")
    
    try:
        # Etapa 1: Extrair procedimentos da descrição cirúrgica
        logger.info("Extraindo procedimentos da descrição cirúrgica")
        resultado_extracao = executar_chain_extracao(texto)
        logger.info(f"Extraídos {len(resultado_extracao.procedimentos_identificados)} procedimentos da descrição cirúrgica")
        
        # Etapa 2: Se houver laudo, extrair procedimentos do laudo anatomopatológico
        resultado_laudo = None
        if laudo_anatomopatologico:
            logger.info("Extraindo procedimentos do laudo anatomopatológico")
            resultado_laudo = executar_extracao_laudo(laudo_anatomopatologico)
            logger.info(f"Extraídos {len(resultado_laudo.procedimentos_laudo)} procedimentos do laudo anatomopatológico")
            
            # Etapa 3: Comparar e corrigir procedimentos (a busca no vector storage é feita internamente)
            logger.info("Comparando e corrigindo procedimentos com base na descrição cirúrgica e no laudo")
            procedimentos_corrigidos = executar_comparacao_procedimentos(
                resultado_extracao.procedimentos_identificados,
                resultado_laudo.procedimentos_laudo
            )
            logger.info(f"Obtidos {len(procedimentos_corrigidos.procedimentos_identificados)} procedimentos corrigidos")
        else:
            logger.info("Laudo anatomopatológico não fornecido, usando apenas descrição cirúrgica")
            
            # Buscar documentos similares diretamente para os procedimentos da descrição cirúrgica
            logger.info("Buscando documentos similares para os procedimentos da descrição cirúrgica")
            documentos_similares = executar_busca_documentos(resultado_extracao.procedimentos_identificados)
            logger.info(f"Encontrados {len(documentos_similares) if documentos_similares else 0} documentos similares")
            
            # Usar os procedimentos da descrição cirúrgica diretamente
            procedimentos_corrigidos = resultado_extracao
        
        # Etapa 4: Decodificar procedimentos
        logger.info("Decodificando procedimentos")
        resultado_decodificacao = executar_chain_decodificacao(
            procedimentos_corrigidos.procedimentos_identificados
        )
        
        # Extrair informações adicionais para classificação final
        # Verificar se há indicação de trauma/acidente no texto
        resultado_decodificacao["entrada_por_trauma"] = verificar_entrada_por_trauma(texto)
        
        # Verificar se os procedimentos são para tratar a mesma doença
        resultado_decodificacao["mesma_doenca"] = verificar_mesma_doenca(
            procedimentos_corrigidos.procedimentos_identificados
        )        
        
        
        # Construir o resultado final
        resultado = {
            "extracao_cirurgia": resultado_extracao,
            "extracao_laudo": resultado_laudo,
            "procedimentos_corrigidos": procedimentos_corrigidos,
            "decodificacao": resultado_decodificacao,
            "tipo_fluxo": "com_peca_anatomica"
        }

        return fluxo_classificacao_final(resultado)
        
    except Exception as e:
        logger.error(f"Erro no fluxo com peça anatômica: {str(e)}")
        # Retornar um resultado parcial em caso de erro
        return {
            "erro": str(e),
            "extracao_cirurgia": resultado_extracao if 'resultado_extracao' in locals() else None,
            "extracao_laudo": resultado_laudo if 'resultado_laudo' in locals() else None,
            "tipo_fluxo": "com_peca_anatomica_com_erro"
        }
        

def fluxo_com_peca_anatomica(texto, laudo_anatomopatologico=None):
    """
    Fluxo para casos com retirada de peça anatômica.
    """
    logger.info("Executando fluxo para casos com retirada de peça anatômica")
    
    try:
        # Etapa 1: Extrair procedimentos da descrição cirúrgica
        logger.info("Extraindo procedimentos da descrição cirúrgica")
        resultado_extracao = executar_chain_extracao(texto)
        logger.info(f"Extraídos {len(resultado_extracao.procedimentos_identificados)} procedimentos da descrição cirúrgica")
        
        # Etapa 2: Se houver laudo, extrair procedimentos do laudo anatomopatológico
        resultado_laudo = None
        if laudo_anatomopatologico:
            logger.info("Extraindo procedimentos do laudo anatomopatológico")
            resultado_laudo = executar_extracao_laudo(laudo_anatomopatologico)
            logger.info(f"Extraídos {len(resultado_laudo.procedimentos_laudo)} procedimentos do laudo anatomopatológico")
            
            # Etapa 3: Comparar e corrigir procedimentos
            logger.info("Comparando e corrigindo procedimentos com base na descrição cirúrgica e no laudo")
            procedimentos_corrigidos = executar_comparacao_procedimentos(
                resultado_extracao.procedimentos_identificados,
                resultado_laudo.procedimentos_laudo
            )
            logger.info(f"Obtidos {len(procedimentos_corrigidos.procedimentos_identificados)} procedimentos corrigidos")
        else:
            logger.info("Laudo anatomopatológico não fornecido, usando apenas descrição cirúrgica")
            
            # Buscar documentos similares diretamente para os procedimentos da descrição cirúrgica
            logger.info("Buscando documentos similares para os procedimentos da descrição cirúrgica")
            documentos_similares = executar_busca_documentos(resultado_extracao.procedimentos_identificados)
            logger.info(f"Encontrados {len(documentos_similares) if documentos_similares else 0} documentos similares")
            
            # Usar os procedimentos da descrição cirúrgica diretamente
            procedimentos_corrigidos = resultado_extracao
        
        # Etapa 4: Decodificar procedimentos
        logger.info("Decodificando procedimentos")
        resultado_decodificacao = executar_chain_decodificacao(
            procedimentos_corrigidos.procedimentos_identificados
        )
        
        # Verificar entrada por trauma e mesma doença separadamente
        entrada_por_trauma = executar_verificacao_trauma(texto)
        mesma_doenca = executar_verificacao_mesma_doenca(procedimentos_corrigidos.procedimentos_identificados)
        
        # Construir o resultado final como um dicionário
        resultado = {
            "extracao_cirurgia": resultado_extracao,
            "extracao_laudo": resultado_laudo,
            "procedimentos_corrigidos": procedimentos_corrigidos,
            "decodificacao": resultado_decodificacao,
            "entrada_por_trauma": entrada_por_trauma,
            "mesma_doenca": mesma_doenca,
            "tipo_fluxo": "com_peca_anatomica"
        }

        # Aplicar a classificação final
        return fluxo_classificacao_final(resultado)
        
    except Exception as e:
        logger.error(f"Erro no fluxo com peça anatômica: {str(e)}")
        # Retornar um resultado parcial em caso de erro
        return {
            "erro": str(e),
            "extracao_cirurgia": resultado_extracao if 'resultado_extracao' in locals() else None,
            "extracao_laudo": resultado_laudo if 'resultado_laudo' in locals() else None,
            "tipo_fluxo": "com_peca_anatomica_com_erro"
        }        


def fluxo_sem_peca_anatomica(texto):
    """Fluxo para casos sem retirada de peça anatômica."""
    logger.info("Executando fluxo para casos sem retirada de peça anatômica")
    
    # Implementação específica para este fluxo
    resultado_extracao = executar_chain_extracao(texto)
    
    # Decodificar procedimentos
    resultado_decodificacao = executar_chain_decodificacao(resultado_extracao.procedimentos_identificados)
    
    # Verificar entrada por trauma e mesma doença separadamente
    entrada_por_trauma = executar_verificacao_trauma(texto)
    mesma_doenca = executar_verificacao_mesma_doenca(resultado_extracao.procedimentos_identificados)
    
    # Construir o resultado como um dicionário
    resultado = {
        "extracao": resultado_extracao,
        "decodificacao": resultado_decodificacao,
        "entrada_por_trauma": entrada_por_trauma,
        "mesma_doenca": mesma_doenca,
        "tipo_fluxo": "sem_peca_anatomica"
    }
    
    # Aplicar a classificação final
    return fluxo_classificacao_final(resultado)


def verificar_entrada_por_trauma(texto):
    """
    Verifica se o texto indica que o paciente deu entrada por trauma/acidente
    utilizando o agente especializado do ProcessadorProcedimentos.
    
    Args:
        texto: Texto da descrição cirúrgica
        
    Returns:
        Boolean indicando se há evidência de trauma/acidente
    """
    logger.info("Iniciando verificação de entrada por trauma")
    return executar_verificacao_trauma(texto)

def verificar_mesma_doenca(procedimentos):
    """
    Verifica se os procedimentos são para tratar a mesma doença
    utilizando o agente especializado do ProcessadorProcedimentos.
    
    Args:
        procedimentos: Lista de procedimentos identificados
        
    Returns:
        Boolean indicando se os procedimentos tratam a mesma doença
    """
    logger.info("Iniciando verificação de mesma doença")
    return executar_verificacao_mesma_doenca(procedimentos)

def fluxo_classificacao_final(resultados):
    """
    Implementa o fluxo de classificação final dos procedimentos conforme o diagrama.
    
    Classifica os procedimentos em:
    - Politrauma: Paciente entrou no hospital por trauma/acidente E tem mais de um procedimento
    - Sequencial: Procedimentos para tratar a mesma doença (sem trauma)
    - Múltipla: Mais de um procedimento cirúrgico para doenças diferentes (sem trauma)
    - Procedimento isolado/único: Um único procedimento (sem trauma)
    
    Args:
        resultados: Dicionário com os resultados das etapas anteriores
        
    Returns:
        Dicionário com os resultados atualizados incluindo a classificação final
    """
    logger.info("Executando fluxo de classificação final dos procedimentos")
    
    try:
        # Obter procedimentos da fonte apropriada
        procedimentos = None
        if "procedimentos_corrigidos" in resultados and hasattr(resultados["procedimentos_corrigidos"], "procedimentos_identificados"):
            procedimentos = resultados["procedimentos_corrigidos"].procedimentos_identificados
        elif "extracao" in resultados and hasattr(resultados["extracao"], "procedimentos_identificados"):
            procedimentos = resultados["extracao"].procedimentos_identificados
        elif "extracao_cirurgia" in resultados and hasattr(resultados["extracao_cirurgia"], "procedimentos_identificados"):
            procedimentos = resultados["extracao_cirurgia"].procedimentos_identificados
        else:
            # Tentar outras formas de obter os procedimentos
            for key in ["procedimentos_corrigidos", "extracao", "extracao_cirurgia"]:
                if key in resultados:
                    if hasattr(resultados[key], "procedimentos_identificados"):
                        procedimentos = resultados[key].procedimentos_identificados
                        break
                    elif isinstance(resultados[key], dict) and "procedimentos_identificados" in resultados[key]:
                        procedimentos = resultados[key]["procedimentos_identificados"]
                        break
        
        if not procedimentos:
            logger.warning("Não foi possível encontrar procedimentos nos resultados")
            procedimentos = []
        
        # Verificar se paciente deu entrada no hospital por trauma/acidente
        entrada_por_trauma = resultados.get("entrada_por_trauma", False)
        
        # Verificar se os procedimentos são para tratar a mesma doença
        mesma_doenca = resultados.get("mesma_doenca", False)
        
        # Verificar se há mais de um procedimento cirúrgico
        multiplos_procedimentos = len(procedimentos) > 1
        
        # Aplicar a lógica do fluxograma corrigida
        classificacao_final = ""
        justificativa = ""
        
        if entrada_por_trauma and multiplos_procedimentos:
            classificacao_final = "politrauma"
            justificativa = "Paciente deu entrada no hospital por trauma/acidente e tem múltiplos procedimentos."
        elif not entrada_por_trauma and multiplos_procedimentos:
            if mesma_doenca:
                classificacao_final = "sequencial"
                justificativa = "Múltiplos procedimentos para tratar a mesma doença."
            else:
                classificacao_final = "multipla"
                justificativa = "Múltiplos procedimentos para tratar doenças diferentes."
        else:
            classificacao_final = "procedimento_isolado"
            justificativa = "Apenas um procedimento cirúrgico identificado ou paciente com trauma e apenas um procedimento."
        
        logger.info(f"Classificação final: {classificacao_final} - {justificativa}")
        
        # Atualizar resultados com a classificação final
        resultados["classificacao_final"] = classificacao_final
        resultados["justificativa_classificacao"] = justificativa
        
        # Adicionar detalhes para depuração e transparência
        resultados["detalhes_classificacao"] = {
            "entrada_por_trauma": entrada_por_trauma,
            "multiplos_procedimentos": multiplos_procedimentos,
            "mesma_doenca": mesma_doenca,
            "numero_procedimentos": len(procedimentos)
        }
        
        return resultados
    
    except Exception as e:
        logger.error(f"Erro no fluxo de classificação final: {str(e)}")
        resultados["erro_classificacao"] = str(e)
        resultados["classificacao_final"] = "não_classificado"
        resultados["justificativa_classificacao"] = f"Erro durante a classificação: {str(e)}"
        return resultados