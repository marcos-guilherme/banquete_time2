import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schemas.modelos_base import (
    InputData, 
    DecodificacaoInput, 
    BuscaDocumentosInput,
    InputDataComLaudo
    )
from schemas.modelos_para_agentes import Procedimento
from fastapi import FastAPI, HTTPException, Body
from src.flows.process_fluxo import processar_texto_e_decidir_fluxo

from src.flows.fluxo_chain import (
    executar_chain_completa, 
    executar_chain_extracao, 
    executar_busca_documentos,
    executar_chain_decodificacao,
    executar_chain_identificacao_peca,
    executar_verificacao_mesma_doenca,
    executar_verificacao_trauma
)
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from schemas.modelos_para_agentes import Procedimento
from loguru import logger



app = FastAPI(
    title="API de Processamento de Procedimentos Médicos",
    description="""
    API para extração, verificação e decodificação de procedimentos médicos em textos.
    
    Endpoints disponíveis:
    - /extrair_procedimentos/: Extrai procedimentos médicos de um texto
    - /verificar_procedimentos/: Verifica procedimentos médicos extraídos
    - /buscar_documentos_similares/: Busca documentos similares no vector store
    - /decodificar_procedimentos/: Decodifica procedimentos verificados
    - /fluxo_completo/: Executa o fluxo completo (extração, verificação, busca e decodificação)
    """,
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"message": "API de Processamento de Procedimentos Médicos", "status": "online"}

@app.post("/extrair_procedimentos/")
async def extrair_procedimentos(data: InputData):
    """
    Extrai procedimentos médicos de um texto.
    
    Args:
        data: Objeto contendo o texto a ser processado
        
    Returns:
        Os procedimentos extraídos
    """
    try:
        texto = data.text if hasattr(data, 'text') else str(data)
        logger.info(f"Recebida solicitação para extrair procedimentos. Tamanho do texto: {len(texto)} caracteres")
        
        resultado = executar_chain_extracao(texto)
        return resultado
    except Exception as e:
        logger.error(f"Erro ao extrair procedimentos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar a solicitação: {str(e)}")


@app.post("/buscar_documentos_similares/")
async def buscar_documentos_similares(data: BuscaDocumentosInput):
    """
    Busca documentos similares no vector store usando embeddings.
    
    Args:
        data: Objeto contendo os procedimentos verificados e opcionalmente o número de documentos a retornar
        
    Returns:
        Lista de documentos similares encontrados
    """
    try:
        procedimentos_verificados = data.procedimentos_verificados
        match_count = data.match_count
        
        logger.info(f"Recebida solicitação para buscar documentos similares. Procedimentos: {len(procedimentos_verificados)}")
        
        resultado = executar_busca_documentos(procedimentos_verificados, match_count)
        return {"documentos_similares": resultado}
    except Exception as e:
        logger.error(f"Erro ao buscar documentos similares: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar a solicitação: {str(e)}")

@app.post("/decodificar_procedimentos/")
async def decodificar_procedimentos(data: DecodificacaoInput):
    """
    Decodifica procedimentos verificados usando documentos similares como referência.
    
    Args:
        data: Objeto contendo os procedimentos verificados e opcionalmente os documentos similares
        
    Returns:
        O resultado da decodificação
    """
    try:
        procedimentos_verificados = data.procedimentos_verificados
        documentos_similares = data.documentos_similares
        
        logger.info(f"Recebida solicitação para decodificar procedimentos. Procedimentos: {len(procedimentos_verificados)}")
        logger.info(f"Documentos similares fornecidos: {documentos_similares is not None}")
        
        resultado = executar_chain_decodificacao(procedimentos_verificados, documentos_similares)
        return resultado
    except Exception as e:
        logger.error(f"Erro ao decodificar procedimentos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar a solicitação: {str(e)}")

@app.post("/fluxo_completo/")
async def fluxo_completo(data: InputData):
    """
    Executa o fluxo completo de processamento de procedimentos médicos.
    
    Este endpoint executa todas as etapas em sequência:
    1. Extração de procedimentos
    2. Verificação de procedimentos
    3. Busca de documentos similares
    4. Decodificação de procedimentos
    
    Args:
        data: Objeto contendo o texto a ser processado
        
    Returns:
        O resultado final do processamento
    """
    try:
        texto = data.text if hasattr(data, 'text') else str(data)
        logger.info(f"Recebida solicitação para processamento completo. Tamanho do texto: {len(texto)} caracteres")
        
        resultado = executar_chain_completa(texto)
        return resultado
    except Exception as e:
        logger.error(f"Erro ao executar fluxo completo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar a solicitação: {str(e)}")
    
    
@app.post("/identificar_peca_anatomica/")
async def identificar_peca_anatomica(data: InputData):
    """
    Identifica se houve retirada de peça anatômica do paciente.
    
    Args:
        data: Objeto contendo o texto a ser processado
        
    Returns:
        O resultado da identificação de peça anatômica (apenas booleano e justificativa)
    """
    try:
        texto = data.text if hasattr(data, 'text') else str(data)
        logger.info(f"Recebida solicitação para identificar peça anatômica. Tamanho do texto: {len(texto)} caracteres")
        
        resultado = executar_chain_identificacao_peca(texto)
        return resultado
    except Exception as e:
        logger.error(f"Erro ao identificar peça anatômica: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar a solicitação: {str(e)}")

    
@app.post("/processar_com_laudo/")
async def processar_com_laudo(data: InputDataComLaudo):
    """
    Processa a descrição cirúrgica e o laudo anatomopatológico, decidindo o fluxo apropriado.
    
    Este endpoint é especialmente útil para casos com retirada de peça anatômica,
    onde o laudo pode fornecer informações complementares importantes.
    
    Args:
        data: Objeto contendo o texto da descrição cirúrgica e opcionalmente o laudo anatomopatológico
        
    Returns:
        Resultado do processamento, incluindo procedimentos corrigidos e complementados
    """
    try:
        texto = data.text
        laudo = data.laudo
        
        logger.info(f"Recebida solicitação para processar com laudo. Tamanho do texto: {len(texto)} caracteres")
        if laudo:
            logger.info(f"Laudo fornecido. Tamanho do laudo: {len(laudo)} caracteres")
        else:
            logger.info("Laudo não fornecido, será usado fluxo sem peça anatômica")
        
        resultado = processar_texto_e_decidir_fluxo(texto, laudo)
        return resultado
    except Exception as e:
        logger.error(f"Erro ao processar com laudo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar a solicitação: {str(e)}")
    
@app.post("/verificar_entrada_por_trauma/")
async def verificar_entrada_por_trauma(data: InputData):
    """
    Verifica se o paciente deu entrada por trauma/acidente.
    
    Args:
        data: Objeto contendo o texto a ser processado
        
    Returns:
        Boolean indicando se há evidência de trauma/acidente e justificativa
    """
    try:
        texto = data.text if hasattr(data, 'text') else str(data)
        logger.info(f"Recebida solicitação para verificar entrada por trauma. Tamanho do texto: {len(texto)} caracteres")
        
        # Executar a verificação
        resultado = executar_verificacao_trauma(texto)
        
        # Se o resultado for um objeto com atributos, retornar como dicionário
        if hasattr(resultado, 'entrada_por_trauma') and hasattr(resultado, 'justificativa'):
            return {
                "entrada_por_trauma": resultado.entrada_por_trauma,
                "justificativa": resultado.justificativa
            }
        # Se for apenas um booleano, retornar com justificativa genérica
        elif isinstance(resultado, bool):
            return {
                "entrada_por_trauma": resultado,
                "justificativa": "Determinado por análise de texto" if resultado else "Não foram encontradas evidências de trauma/acidente"
            }
        # Caso contrário, retornar o resultado diretamente
        else:
            return resultado
            
    except Exception as e:
        logger.error(f"Erro ao verificar entrada por trauma: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar a solicitação: {str(e)}")


@app.post("/verificar_mesma_doenca/")
async def verificar_mesma_doenca(data: BuscaDocumentosInput):
    """
    Verifica se os procedimentos são para tratar a mesma doença.
    
    Args:
        data: Objeto contendo a lista de procedimentos
        
    Returns:
        Boolean indicando se os procedimentos tratam a mesma doença e justificativa
    """
    try:
        procedimentos = data.procedimentos_verificados
        logger.info(f"Recebida solicitação para verificar mesma doença. Procedimentos: {len(procedimentos)}")
        
        # Executar a verificação
        resultado = executar_verificacao_mesma_doenca(procedimentos)
        
        # Se o resultado for um objeto com atributos, retornar como dicionário
        if hasattr(resultado, 'mesma_doenca') and hasattr(resultado, 'justificativa'):
            return {
                "mesma_doenca": resultado.mesma_doenca,
                "justificativa": resultado.justificativa
            }
        # Se for apenas um booleano, retornar com justificativa genérica
        elif isinstance(resultado, bool):
            return {
                "mesma_doenca": resultado,
                "justificativa": "Procedimentos tratam a mesma doença" if resultado else "Procedimentos tratam doenças diferentes"
            }
        # Caso contrário, retornar o resultado diretamente
        else:
            return {"mesma_doenca": resultado}
            
    except Exception as e:
        logger.error(f"Erro ao verificar mesma doença: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar a solicitação: {str(e)}")
    
@app.post("/classificacao_final/")
async def classificacao_final(data: InputData):
    """
    Executa o fluxo completo e retorna a classificação final dos procedimentos.
    
    Este endpoint executa todas as etapas e retorna a classificação conforme o fluxograma:
    - Politrauma: Paciente entrou no hospital por trauma/acidente
    - Sequencial: Procedimentos para tratar a mesma doença
    - Múltipla: Mais de um procedimento cirúrgico para doenças diferentes
    - Procedimento isolado/único: Um único procedimento
    
    Args:
        data: Objeto contendo o texto a ser processado
        
    Returns:
        A classificação final e sua justificativa
    """
    try:
        texto = data.text if hasattr(data, 'text') else str(data)
        logger.info(f"Recebida solicitação para classificação final. Tamanho do texto: {len(texto)} caracteres")
        
        # Importar a função de processamento completo
        from src.flows.process_fluxo import processar_texto_e_decidir_fluxo
        
        # Executar o processamento completo
        resultado = processar_texto_e_decidir_fluxo(texto)
        
        # Extrair apenas as informações relevantes para a resposta
        resposta = {
            "classificacao_final": resultado.get("classificacao_final", "não_classificado"),
            "justificativa": resultado.get("justificativa_classificacao", "Não foi possível determinar uma justificativa."),
            "detalhes": resultado.get("detalhes_classificacao", {})
        }
        
        return resposta
            
    except Exception as e:
        logger.error(f"Erro ao executar classificação final: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar a solicitação: {str(e)}")