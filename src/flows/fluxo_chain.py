from schemas.modelos_para_agentes import (
    ProcedimentoExtracao, 
    Decodificacao, 
    IdentificacaoPecaAnatomica,
    VerificacaoTrauma,
    VerificacaoMesmaDoenca,
    ExtratorLaudoAnatomopatologico
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from openai import OpenAI
from functions import load_prompt
from loguru import logger
import dotenv
import os
from supabase import create_client, Client
from typing import List, Dict, Any, Optional

dotenv.load_dotenv()
open_ai_key = os.getenv("OPENAI_API_KEY")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SERVICE_KEY_SUPABASE")

# Configuração do Supabase
supabase = create_client(supabase_url, supabase_key)
TABLE = "tabela_embeddings_grupo_02_04"
FUNC_NAME = "match_procedimentos"

class ProcessadorProcedimentos:
    """
    Processador simplificado para extração, verificação e decodificação de procedimentos médicos
    usando a técnica de saída estruturada do LangChain.
    """
    
    def __init__(self, model_name="gpt-4o-mini", temperature=0):
        """Inicializa o processador com configurações do modelo."""
        self.llm = ChatOpenAI(openai_api_key=open_ai_key, model=model_name, temperature=temperature)
        self.embeddings = OpenAIEmbeddings(openai_api_key=open_ai_key)
        
        # Carregar prompts
        self.prompt_extracao = load_prompt(r"prompts\system_extracao_procedimentos.txt")
        self.prompt_decodificacao = load_prompt(r"prompts\system_decodificacao.txt")
        self.prompt_identificacao_peca = load_prompt(r"prompts\system_identificacao_peca_anatomica.txt")
        self.prompt_extracao_laudo = load_prompt(r"prompts\system_extracao_procedimentos_laudo.txt")
        self.prompt_comparacao_procedimentos = load_prompt(r"prompts\system_comparacao_procedimentos.txt")
        self.prompt_verificacao_trauma = load_prompt(r"prompts\system_verificacao_trauma.txt")
        self.prompt_verificacao_mesma_doenca = load_prompt(r"prompts\system_verificacao_mesma_doenca.txt")
        
        # Criar os modelos com saída estruturada
        self.extrator = self._criar_extrator()
        self.decodificador = self._criar_decodificador()
        self.identificador_peca = self._criar_identificador_peca()
        self.extrator_laudo = self._criar_extrator_laudo()
        self.comparador = self._criar_comparador_procedimentos()  # Renomeado para evitar conflito
        self.verificador_trauma = self._criar_verificador_trauma()
        self.verificador_mesma_doenca = self._criar_verificador_mesma_doenca()
     
    def _formatar_procedimentos_para_verificacao(self, procedimentos):
            """
            Formata os procedimentos para uso no verificador de mesma doença.
            
            Args:
                procedimentos: Lista de procedimentos identificados
                
            Returns:
                String formatada com os procedimentos
            """
            if not procedimentos:
                return "Nenhum procedimento identificado."
            
            resultado = []
            
            # Verificar se procedimentos é um objeto com atributo procedimentos_identificados
            if hasattr(procedimentos, 'procedimentos_identificados'):
                procedimentos = procedimentos.procedimentos_identificados
            
            # Processar a lista de procedimentos
            if isinstance(procedimentos, list):
                for i, proc in enumerate(procedimentos, 1):
                    if isinstance(proc, dict):
                        linha = f"{i}. {proc.get('procedimento', 'N/A')}"
                        if 'descricao' in proc and proc['descricao']:
                            linha += f": {proc['descricao']}"
                        if 'diagnostico' in proc and proc['diagnostico']:
                            linha += f"\n   Diagnóstico: {proc['diagnostico']}"
                        resultado.append(linha)
                    elif hasattr(proc, 'procedimento'):
                        linha = f"{i}. {proc.procedimento}"
                        if hasattr(proc, 'descricao') and proc.descricao:
                            linha += f": {proc.descricao}"
                        if hasattr(proc, 'diagnostico') and proc.diagnostico:
                            linha += f"\n   Diagnóstico: {proc.diagnostico}"
                        resultado.append(linha)
                    else:
                        resultado.append(f"{i}. {str(proc)}")
            # Caso seja uma string, retornar diretamente
            elif isinstance(procedimentos, str):
                return procedimentos
            
            return "\n".join(resultado) if resultado else "Nenhum procedimento identificado."     
     
     
    def _criar_verificador_mesma_doenca(self):
        """Cria o verificador se os procedimentos são para tratar a mesma doença."""
        prompt = ChatPromptTemplate.from_template(
            self.prompt_verificacao_mesma_doenca + "\n\nProcedimentos:\n{procedimentos}"
        )
        return prompt | self.llm.with_structured_output(VerificacaoMesmaDoenca)
        
    def _criar_verificador_trauma(self):
        """Cria o verificador de entrada por trauma/acidente."""
        prompt = ChatPromptTemplate.from_template(
            self.prompt_verificacao_trauma + "\n\nTexto da descrição cirúrgica:\n{texto}"
        )
        return prompt | self.llm.with_structured_output(VerificacaoTrauma)    
    
    def _criar_extrator(self):
        """Cria o extrator de procedimentos."""
        prompt = ChatPromptTemplate.from_template(
            self.prompt_extracao + "\n\nTexto:\n{text}"
        )
        return prompt | self.llm.with_structured_output(ProcedimentoExtracao)
    
    def _criar_extrator_laudo(self):
        """Cria o extrator de procedimentos de laudo."""
        prompt = ChatPromptTemplate.from_template(
            self.prompt_extracao_laudo + "\n\nLaudo Anatomopatológico:\n{laudo}"
        )
        return prompt | self.llm.with_structured_output(ExtratorLaudoAnatomopatologico)   
    
    def extrair_procedimentos_laudo(self, laudo):
        """Extrai procedimentos do laudo anatomopatológico."""
        logger.info("Extraindo procedimentos do laudo anatomopatológico")
        return self.extrator_laudo.invoke({"laudo": laudo})
    
    def comparar_e_corrigir_procedimentos(self, procedimentos_cirurgia, procedimentos_laudo, documentos_similares=None):
        """
        Compara e corrige procedimentos extraídos da descrição cirúrgica com base no laudo anatomopatológico.
        
        Args:
            procedimentos_cirurgia: Procedimentos extraídos da descrição cirúrgica
            procedimentos_laudo: Procedimentos extraídos do laudo anatomopatológico
            documentos_similares: Documentos similares do vector storage (opcional)
            
        Returns:
            Procedimentos corrigidos e complementados
        """
        logger.info("Comparando e corrigindo procedimentos")
        
        # Se não foram fornecidos documentos similares, buscar no vector store
        if documentos_similares is None:
            logger.info("Buscando documentos similares no vector store")
            
            # Extrair termos relevantes de ambas as fontes para melhorar a busca
            termos_busca = []
            
            # Extrair termos da descrição cirúrgica
            if procedimentos_cirurgia:
                if hasattr(procedimentos_cirurgia, 'procedimentos_identificados'):
                    for proc in procedimentos_cirurgia.procedimentos_identificados:
                        if hasattr(proc, 'procedimento'):
                            termos_busca.append(proc.procedimento)
                        elif isinstance(proc, dict) and 'procedimento' in proc:
                            termos_busca.append(proc['procedimento'])
                elif isinstance(procedimentos_cirurgia, list):
                    for proc in procedimentos_cirurgia:
                        if hasattr(proc, 'procedimento'):
                            termos_busca.append(proc.procedimento)
                        elif isinstance(proc, dict) and 'procedimento' in proc:
                            termos_busca.append(proc['procedimento'])
            
            # Extrair termos do laudo anatomopatológico
            if procedimentos_laudo:
                if hasattr(procedimentos_laudo, 'procedimentos_laudo'):
                    for proc in procedimentos_laudo.procedimentos_laudo:
                        if hasattr(proc, 'procedimento'):
                            termos_busca.append(proc.procedimento)
                        elif isinstance(proc, dict) and 'procedimento' in proc:
                            termos_busca.append(proc['procedimento'])
                        
                        # Também incluir peças anatômicas na busca
                        if hasattr(proc, 'peca_anatomica'):
                            termos_busca.append(proc.peca_anatomica)
                        elif isinstance(proc, dict) and 'peca_anatomica' in proc:
                            termos_busca.append(proc['peca_anatomica'])
                        
                        # Incluir diagnósticos relevantes
                        if hasattr(proc, 'diagnostico'):
                            termos_busca.append(proc.diagnostico)
                        elif isinstance(proc, dict) and 'diagnostico' in proc:
                            termos_busca.append(proc['diagnostico'])
                elif isinstance(procedimentos_laudo, list):
                    for proc in procedimentos_laudo:
                        if hasattr(proc, 'procedimento'):
                            termos_busca.append(proc.procedimento)
                        elif isinstance(proc, dict) and 'procedimento' in proc:
                            termos_busca.append(proc['procedimento'])
            
            # Remover duplicatas e termos vazios
            termos_busca = [termo for termo in termos_busca if termo and termo.strip()]
            termos_busca = list(set(termos_busca))
            
            logger.info(f"Termos de busca extraídos: {termos_busca}")
            
            # Construir a query para busca
            query = " ".join(termos_busca)
            
            # Buscar documentos similares
            try:
                # Gerar embedding para a query combinada
                query_embedding = self.gerar_embedding(query)
                
                # Chamar a função RPC do Supabase para buscar documentos similares
                response = supabase.rpc(FUNC_NAME, {
                    'query_embedding': query_embedding,
                    'match_count': 10  # Aumentar para ter mais contexto
                }).execute()
                
                if hasattr(response, 'data') and response.data:
                    documentos_similares = response.data
                    logger.info(f"Encontrados {len(documentos_similares)} documentos similares")
                else:
                    logger.warning("Nenhum documento similar encontrado")
                    documentos_similares = []
                    
            except Exception as e:
                logger.error(f"Erro ao buscar documentos similares: {str(e)}")
                documentos_similares = []
        
        # Formatar documentos similares para uso no prompt
        documentos_formatados = self.formatar_documentos_similares(documentos_similares)
        
        # Preparar os procedimentos da cirurgia para o comparador
        procedimentos_cirurgia_formatados = self._formatar_procedimentos_para_comparacao(procedimentos_cirurgia)
        
        # Preparar os procedimentos do laudo para o comparador
        procedimentos_laudo_formatados = self._formatar_procedimentos_laudo_para_comparacao(procedimentos_laudo)
        
        # Invocar o comparador
        logger.info("Invocando o comparador de procedimentos")
        resultado = self.comparador.invoke({  # Corrigido para usar self.comparador
            "procedimentos_cirurgia": procedimentos_cirurgia_formatados,
            "procedimentos_laudo": procedimentos_laudo_formatados,
            "documentos_similares": documentos_formatados
        })
        
        logger.info(f"Comparação concluída. Identificados {len(resultado.procedimentos_identificados)} procedimentos corrigidos")
        return resultado

    def _formatar_procedimentos_para_comparacao(self, procedimentos):
        """
        Formata os procedimentos da descrição cirúrgica para uso no comparador.
        
        Args:
            procedimentos: Procedimentos extraídos da descrição cirúrgica
            
        Returns:
            String formatada com os procedimentos
        """
        if not procedimentos:
            return "Nenhum procedimento identificado na descrição cirúrgica."
        
        resultado = []
        
        # Verificar se procedimentos é um objeto com atributo procedimentos_identificados
        if hasattr(procedimentos, 'procedimentos_identificados'):
            for i, proc in enumerate(procedimentos.procedimentos_identificados, 1):
                if hasattr(proc, 'procedimento') and hasattr(proc, 'descricao'):
                    resultado.append(f"{i}. {proc.procedimento}: {proc.descricao}")
                elif isinstance(proc, dict):
                    resultado.append(f"{i}. {proc.get('procedimento', 'N/A')}: {proc.get('descricao', 'N/A')}")
        # Verificar se procedimentos é uma lista
        elif isinstance(procedimentos, list):
            for i, proc in enumerate(procedimentos, 1):
                if hasattr(proc, 'procedimento') and hasattr(proc, 'descricao'):
                    resultado.append(f"{i}. {proc.procedimento}: {proc.descricao}")
                elif isinstance(proc, dict):
                    resultado.append(f"{i}. {proc.get('procedimento', 'N/A')}: {proc.get('descricao', 'N/A')}")
        # Caso seja uma string, retornar diretamente
        elif isinstance(procedimentos, str):
            return procedimentos
        
        return "\n".join(resultado) if resultado else "Nenhum procedimento identificado na descrição cirúrgica."

    def _formatar_procedimentos_laudo_para_comparacao(self, procedimentos_laudo):
        """
        Formata os procedimentos do laudo anatomopatológico para uso no comparador.
        
        Args:
            procedimentos_laudo: Procedimentos extraídos do laudo anatomopatológico
            
        Returns:
            String formatada com os procedimentos do laudo
        """
        if not procedimentos_laudo:
            return "Nenhum procedimento identificado no laudo anatomopatológico."
        
        resultado = []
        
        # Verificar se procedimentos_laudo é um objeto com atributo procedimentos_laudo
        if hasattr(procedimentos_laudo, 'procedimentos_laudo'):
            for i, proc in enumerate(procedimentos_laudo.procedimentos_laudo, 1):
                if hasattr(proc, 'procedimento'):
                    linha = f"{i}. {proc.procedimento}"
                    if hasattr(proc, 'descricao') and proc.descricao:
                        linha += f": {proc.descricao}"
                    if hasattr(proc, 'peca_anatomica') and proc.peca_anatomica:
                        linha += f"\n   Peça anatômica: {proc.peca_anatomica}"
                    if hasattr(proc, 'diagnostico') and proc.diagnostico:
                        linha += f"\n   Diagnóstico: {proc.diagnostico}"
                    resultado.append(linha)
                elif isinstance(proc, dict):
                    linha = f"{i}. {proc.get('procedimento', 'N/A')}"
                    if 'descricao' in proc and proc['descricao']:
                        linha += f": {proc['descricao']}"
                    if 'peca_anatomica' in proc and proc['peca_anatomica']:
                        linha += f"\n   Peça anatômica: {proc['peca_anatomica']}"
                    if 'diagnostico' in proc and proc['diagnostico']:
                        linha += f"\n   Diagnóstico: {proc['diagnostico']}"
                    resultado.append(linha)
        # Verificar se procedimentos_laudo é uma lista
        elif isinstance(procedimentos_laudo, list):
            for i, proc in enumerate(procedimentos_laudo, 1):
                if hasattr(proc, 'procedimento'):
                    linha = f"{i}. {proc.procedimento}"
                    if hasattr(proc, 'descricao') and proc.descricao:
                        linha += f": {proc.descricao}"
                    if hasattr(proc, 'peca_anatomica') and proc.peca_anatomica:
                        linha += f"\n   Peça anatômica: {proc.peca_anatomica}"
                    if hasattr(proc, 'diagnostico') and proc.diagnostico:
                        linha += f"\n   Diagnóstico: {proc.diagnostico}"
                    resultado.append(linha)
                elif isinstance(proc, dict):
                    linha = f"{i}. {proc.get('procedimento', 'N/A')}"
                    if 'descricao' in proc and proc['descricao']:
                        linha += f": {proc['descricao']}"
                    if 'peca_anatomica' in proc and proc['peca_anatomica']:
                        linha += f"\n   Peça anatômica: {proc['peca_anatomica']}"
                    if 'diagnostico' in proc and proc['diagnostico']:
                        linha += f"\n   Diagnóstico: {proc['diagnostico']}"
                    resultado.append(linha)
        # Caso seja uma string, retornar diretamente
        elif isinstance(procedimentos_laudo, str):
            return procedimentos_laudo
        
        return "\n".join(resultado) if resultado else "Nenhum procedimento identificado no laudo anatomopatológico."

    def _criar_comparador_procedimentos(self):
       """Cria o comparador de procedimentos entre descrição cirúrgica e laudo anatomopatológico."""
       prompt = ChatPromptTemplate.from_template(
           self.prompt_comparacao_procedimentos + 
           "\n\nProcedimentos da Descrição Cirúrgica:\n{procedimentos_cirurgia}" +
           "\n\nProcedimentos do Laudo Anatomopatológico:\n{procedimentos_laudo}" +
           "\n\nDocumentos Similares:\n{documentos_similares}"
       )
       return prompt | self.llm.with_structured_output(ProcedimentoExtracao)
    
    def _criar_decodificador(self):
        """Cria o decodificador de procedimentos."""
        prompt = ChatPromptTemplate.from_template(
            self.prompt_decodificacao + "\n\nProcedimentos Verificados:\n{procedimentos_verificados}\n\nDocumentos Similares:\n{documentos_similares}"
        )
        return prompt | self.llm.with_structured_output(Decodificacao)
    
    def _criar_identificador_peca(self):
        """Cria o identificador de peça anatômica."""
        prompt = ChatPromptTemplate.from_template(
            self.prompt_identificacao_peca + "\n\nTexto:\n{text}"
        )
        return prompt | self.llm.with_structured_output(IdentificacaoPecaAnatomica)
    
    def extrair_procedimentos(self, texto):
        """Extrai procedimentos do texto."""
        logger.info("Extraindo procedimentos do texto")
        return self.extrator.invoke({"text": texto})
    
    def gerar_embedding(self, texto):
        """
        Gera um embedding para o texto usando o modelo da OpenAI.
        
        Args:
            texto: Texto para gerar o embedding
            
        Returns:
            Embedding do texto
        """
        logger.info("Gerando embedding para o texto")
        
        client = OpenAI(api_key=open_ai_key)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texto
        )
        
        return response.data[0].embedding
    
    def processar_texto_completo(self, texto):
        """
        Processa o texto completo, executando todas as etapas em sequência.
        
        Args:
            texto: O texto a ser processado
            
        Returns:
            O resultado final da decodificação
        """
        logger.info(f"Processando texto completo: {texto[:100]}...")
        
        try:
            # Etapa 1: Extração
            resultado_extracao = self.extrair_procedimentos(texto)
            logger.debug(f"Resultado da extração: {resultado_extracao}")
            
            # Etapa 2: Busca de documentos similares
            documentos_similares = self.buscar_documentos_similares(
                resultado_extracao.procedimentos_identificados
            )
            logger.debug(f"Encontrados {len(documentos_similares)} documentos similares")
            
            # Etapa 3: Decodificação
            resultado_decodificacao = self.decodificar_procedimentos(
                resultado_extracao.procedimentos_identificados,
                documentos_similares
            )
            logger.debug(f"Resultado da decodificação: {resultado_decodificacao}")
            
            return resultado_decodificacao
        
        except Exception as e:
            logger.error(f"Erro ao processar texto completo: {str(e)}")
            # Retornar um objeto Decodificacao vazio em caso de erro
            return Decodificacao(
                nome_procedimentos="Erro ao processar texto completo",
                codigo_procedimentos="N/A",
                tratar_cancer=False
            )
    
    def buscar_documentos_similares(self, procedimentos_verificados, match_count=15):
        """
        Busca documentos similares no vector store usando embeddings.
        
        Args:
            procedimentos_verificados: Lista de procedimentos verificados
            match_count: Número de documentos similares a serem retornados
            
        Returns:
            Lista de documentos similares encontrados
        """
        logger.info("Buscando documentos similares no vector store")
        
        try:
            # Verificar se procedimentos_verificados é uma lista
            if not isinstance(procedimentos_verificados, list):
                logger.warning(f"procedimentos_verificados não é uma lista: {type(procedimentos_verificados)}")
                if hasattr(procedimentos_verificados, 'procedimentos_verificados'):
                    procedimentos_verificados = procedimentos_verificados.procedimentos_verificados
                else:
                    procedimentos_verificados = [procedimentos_verificados]
            
            # Extrair os nomes dos procedimentos verificados
            nomes_procedimentos = []
            for proc in procedimentos_verificados:
                try:
                    if isinstance(proc, dict) and "procedimento" in proc:
                        nomes_procedimentos.append(proc["procedimento"])
                    elif hasattr(proc, "procedimento"):
                        nomes_procedimentos.append(proc.procedimento)
                    else:
                        logger.warning(f"Não foi possível extrair o nome do procedimento: {proc}")
                except Exception as e:
                    logger.error(f"Erro ao extrair nome do procedimento: {str(e)}")
            
            # Se não conseguimos extrair nenhum nome, retornar lista vazia
            if not nomes_procedimentos:
                logger.warning("Não foi possível extrair nomes de procedimentos")
                return []
            
            # Criar uma query combinando os nomes dos procedimentos
            query = " ".join(nomes_procedimentos)
            logger.debug(f"Query para busca de embeddings: {query}")
            
            # Gerar o embedding para a query
            try:
                query_embedding = self.gerar_embedding(query)
            except Exception as e:
                logger.error(f"Erro ao gerar embedding: {str(e)}")
                return []
            
            try:
                # Chamar a função RPC do Supabase para buscar documentos similares
                response = supabase.rpc(FUNC_NAME, {
                    'query_embedding': query_embedding,
                    'match_count': match_count
                }).execute()
                
                # Verificar se a resposta foi bem-sucedida
                if hasattr(response, 'data') and response.data:
                    logger.info(f"Encontrados {len(response.data)} documentos similares")
                    return response.data
                else:
                    logger.warning("Nenhum documento similar encontrado")
                    return []
            
            except Exception as e:
                logger.error(f"Erro ao buscar documentos similares: {str(e)}")
                return []
        
        except Exception as e:
            logger.error(f"Erro geral ao buscar documentos similares: {str(e)}")
            return []
    
    def formatar_documentos_similares(self, documentos):
        """
        Formata os documentos similares para um formato mais legível.
        
        Args:
            documentos: Lista de documentos similares
            
        Returns:
            String formatada com os documentos similares
        """
        if not documentos:
            return "Nenhum documento similar encontrado."
        
        documentos_formatados = []
        for doc in documentos:
            # Verificar se doc é um dicionário
            if not isinstance(doc, dict):
                logger.warning(f"Documento não é um dicionário: {doc}")
                continue
                
            # Criar a string formatada para o documento
            try:
                doc_str = ""  # Inicializar a variável para cada documento
                doc_str += f"Código: {doc.get('codigo_procedimento', 'N/A')}\n"
                doc_str += f"Nome: {doc.get('nome_procedimento', 'N/A')}\n"
                doc_str += f"Descrição: {doc.get('descricao_procedimento', 'N/A')}\n"
                documentos_formatados.append(doc_str)
            except Exception as e:
                logger.error(f"Erro ao formatar documento: {str(e)}")
                logger.error(f"Documento: {doc}")
                # Adicionar uma entrada genérica para não quebrar o fluxo
                documentos_formatados.append(f"Documento: {str(doc)}")
        
        # Se não conseguimos formatar nenhum documento, retornar uma mensagem
        if not documentos_formatados:
            return "Não foi possível formatar os documentos similares."
        
        logger.info(f"Documentos formatados: {documentos_formatados}")
        return "\n\n".join(documentos_formatados)

    def decodificar_procedimentos(self, procedimentos_verificados, documentos_similares=None):
        """
        Decodifica os procedimentos verificados usando documentos similares como referência.
        
        Args:
            procedimentos_verificados: Lista de procedimentos verificados
            documentos_similares: Lista de documentos similares ou string formatada (opcional)
                                Se não for fornecido, será realizada a busca no vector store
        
        Returns:
            Decodificação dos procedimentos com seus respectivos códigos
        """
        logger.info("Decodificando procedimentos verificados")
        
        try:
            # Se não foram fornecidos documentos similares, buscar no vector store
            if documentos_similares is None:
                documentos_similares = self.buscar_documentos_similares(procedimentos_verificados)
                logger.debug(f"Documentos similares buscados: {len(documentos_similares) if isinstance(documentos_similares, list) else 'não é lista'}")
            
            # Se documentos_similares é uma lista, formatá-la para uma string
            documentos_formatados = ""
            if isinstance(documentos_similares, list):
                documentos_formatados = self.formatar_documentos_similares(documentos_similares)
                logger.debug(f"Documentos formatados (primeiros 200 caracteres): {documentos_formatados[:200]}")
            elif isinstance(documentos_similares, str):
                documentos_formatados = documentos_similares
                logger.debug(f"Documentos já formatados (primeiros 200 caracteres): {documentos_formatados[:200]}")
            else:
                logger.warning(f"Formato de documentos_similares não reconhecido: {type(documentos_similares)}")
                documentos_formatados = str(documentos_similares)
            
            # Verificar se procedimentos_verificados é uma lista
            if not isinstance(procedimentos_verificados, list):
                logger.warning(f"procedimentos_verificados não é uma lista: {type(procedimentos_verificados)}")
                if hasattr(procedimentos_verificados, 'procedimentos_verificados'):
                    procedimentos_verificados = procedimentos_verificados.procedimentos_verificados
                else:
                    procedimentos_verificados = [procedimentos_verificados]
            
            # Invocar o decodificador
            return self.decodificador.invoke({
                "procedimentos_verificados": procedimentos_verificados,
                "documentos_similares": documentos_formatados
            })
        except Exception as e:
            logger.error(f"Erro ao decodificar procedimentos: {str(e)}")
            # Retornar um objeto Decodificacao vazio em caso de erro
            return Decodificacao(
                nome_procedimentos=["Erro ao decodificar procedimentos"],
                codigo_procedimentos=["N/A"]
            )
    
    def identificar_peca_anatomica(self, texto):
        """
        Identifica a peça anatômica retirada do paciente.
        """
        logger.info("Identificando peça anatômica retirada do paciente")
        return self.identificador_peca.invoke({"text": texto})
    
    def verificar_entrada_por_trauma(self, texto):
        """
        Verifica se o texto indica que o paciente deu entrada por trauma/acidente
        utilizando um agente especializado baseado em LLM.
        
        Args:
            texto: Texto da descrição cirúrgica
            
        Returns:
            Boolean indicando se há evidência de trauma/acidente
        """
        logger.info("Verificando entrada por trauma com agente especializado")
        
        try:
            # Invocar o verificador de trauma
            resultado = self.verificador_trauma.invoke({"texto": texto})
            
            logger.info(f"Resultado da verificação de trauma: {resultado.entrada_por_trauma} - {resultado.justificativa}")
            
            return resultado.entrada_por_trauma
            
        except Exception as e:
            logger.error(f"Erro na verificação de entrada por trauma: {str(e)}")
            
            # Fallback para o método baseado em palavras-chave
            logger.info("Utilizando método de fallback baseado em palavras-chave")
            return self.verificar_entrada_por_trauma_palavras_chave(texto)

    def verificar_entrada_por_trauma_palavras_chave(self, texto):
        """
        Método de fallback que verifica se o texto indica trauma/acidente
        baseado em palavras-chave.
        
        Args:
            texto: Texto da descrição cirúrgica
            
        Returns:
            Boolean indicando se há evidência de trauma/acidente
        """
        # Palavras-chave que podem indicar trauma/acidente
        palavras_trauma = [
            "trauma", "acidente", "queda", "colisão", "fratura", "politrauma",
            "atropelamento", "ferimento", "lesão traumática", "contusão",
            "traumatismo", "acidentado", "impacto", "explosão", "queimadura",
            "esmagamento", "perfuração", "laceração", "amputação traumática"
        ]
        
        texto_lower = texto.lower()
        for palavra in palavras_trauma:
            if palavra in texto_lower:
                logger.info(f"Identificada entrada por trauma/acidente (palavras-chave): '{palavra}'")
                return True
        
        return False
    
    def verificar_mesma_doenca(self, procedimentos):
        """
        Verifica se os procedimentos são para tratar a mesma doença
        utilizando um agente especializado baseado em LLM.
        
        Args:
            procedimentos: Lista de procedimentos identificados
            
        Returns:
            Boolean indicando se os procedimentos tratam a mesma doença
        """
        logger.info("Verificando se procedimentos tratam a mesma doença com agente especializado")
        
        # Se houver apenas um procedimento, consideramos como mesma doença
        if not procedimentos or (isinstance(procedimentos, list) and len(procedimentos) <= 1):
            logger.info("Apenas um procedimento identificado, considerando como mesma doença")
            return True
        
        try:
            # Formatar os procedimentos para o verificador
            procedimentos_formatados = self._formatar_procedimentos_para_verificacao(procedimentos)
            
            # Invocar o verificador de mesma doença
            resultado = self.verificador_mesma_doenca.invoke({"procedimentos": procedimentos_formatados})
            
            logger.info(f"Resultado da verificação de mesma doença: {resultado.mesma_doenca} - {resultado.justificativa}")
            
            return resultado.mesma_doenca
            
        except Exception as e:
            logger.error(f"Erro na verificação de mesma doença: {str(e)}")
            
            # Fallback para o método baseado em diagnósticos
            logger.info("Utilizando método de fallback baseado em diagnósticos")
            return self.verificar_mesma_doenca_diagnosticos(procedimentos)    

    def verificar_mesma_doenca_diagnosticos(self, procedimentos):
        """
        Método de fallback que verifica se os procedimentos são para a mesma doença
        baseado nos diagnósticos associados.
        
        Args:
            procedimentos: Lista de procedimentos identificados
            
        Returns:
            Boolean indicando se os procedimentos tratam a mesma doença
        """
        # Se houver apenas um procedimento, consideramos como mesma doença
        if not procedimentos or (isinstance(procedimentos, list) and len(procedimentos) <= 1):
            return True
        
        # Verificar se procedimentos é um objeto com atributo procedimentos_identificados
        if hasattr(procedimentos, 'procedimentos_identificados'):
            procedimentos = procedimentos.procedimentos_identificados
        
        # Verificar se os procedimentos têm diagnósticos ou indicações semelhantes
        diagnosticos = set()
        for proc in procedimentos:
            if isinstance(proc, dict) and "diagnostico" in proc and proc["diagnostico"]:
                diagnosticos.add(proc["diagnostico"])
            elif hasattr(proc, "diagnostico") and proc.diagnostico:
                diagnosticos.add(proc.diagnostico)
        
        # Se todos os procedimentos têm o mesmo diagnóstico ou não têm diagnóstico
        mesma_doenca = len(diagnosticos) <= 1
        logger.info(f"Verificação de mesma doença (fallback): {mesma_doenca} (diagnósticos: {diagnosticos})")
        return mesma_doenca

# Funções de conveniência para uso direto
def executar_chain_completa(texto: str):
    """Executa o fluxo completo de processamento."""
    processador = ProcessadorProcedimentos()
    return processador.processar_texto_completo(texto)

def executar_chain_identificacao_peca(texto: str):
    """Executa apenas a etapa de identificação de peça anatômica."""
    processador = ProcessadorProcedimentos()
    return processador.identificar_peca_anatomica(texto)

def executar_chain_extracao(texto: str):
    """Executa apenas a etapa de extração."""
    processador = ProcessadorProcedimentos()
    return processador.extrair_procedimentos(texto)

def executar_busca_documentos(procedimentos_verificados, match_count=10):
    """
    Executa apenas a etapa de busca de documentos similares.
    
    Args:
        procedimentos_verificados: Lista de procedimentos verificados
        match_count: Número de documentos similares a serem retornados
        
    Returns:
        Lista de documentos similares encontrados
    """
    processador = ProcessadorProcedimentos()
    return processador.buscar_documentos_similares(procedimentos_verificados, match_count)

def executar_chain_decodificacao(procedimentos_verificados, documentos_similares=None):
    """
    Executa apenas a etapa de decodificação.
    
    Args:
        procedimentos_verificados: Lista de procedimentos verificados
        documentos_similares: Lista de documentos similares ou string formatada (opcional)
            Se não for fornecido, será realizada a busca no vector store
            
    Returns:
        O resultado da decodificação
    """
    processador = ProcessadorProcedimentos()
    return processador.decodificar_procedimentos(procedimentos_verificados, documentos_similares)

def executar_extracao_laudo(laudo: str):
    """
    Executa apenas a etapa de extração de procedimentos do laudo anatomopatológico.
    
    Args:
        laudo: Texto do laudo anatomopatológico
        
    Returns:
        Procedimentos extraídos do laudo
    """
    processador = ProcessadorProcedimentos()
    return processador.extrair_procedimentos_laudo(laudo)

def executar_comparacao_procedimentos(procedimentos_cirurgia, procedimentos_laudo, documentos_similares=None):
    """
    Executa apenas a etapa de comparação e correção de procedimentos.
    
    Args:
        procedimentos_cirurgia: Procedimentos extraídos da descrição cirúrgica
        procedimentos_laudo: Procedimentos extraídos do laudo anatomopatológico
        documentos_similares: Documentos similares do vector storage (opcional)
        
    Returns:
        Procedimentos corrigidos e complementados
    """
    processador = ProcessadorProcedimentos()
    return processador.comparar_e_corrigir_procedimentos(
        procedimentos_cirurgia,
        procedimentos_laudo,
        documentos_similares
    )
    
def executar_verificacao_trauma(texto: str):
    """
    Executa apenas a etapa de verificação de entrada por trauma/acidente.
    
    Args:
        texto: Texto da descrição cirúrgica
        
    Returns:
        Boolean indicando se há evidência de trauma/acidente
    """
    processador = ProcessadorProcedimentos()
    return processador.verificar_entrada_por_trauma(texto)

def executar_verificacao_mesma_doenca(procedimentos):
    """
    Executa apenas a etapa de verificação: se os procedimentos são para tratar a mesma doença.
    
    Args:
        procedimentos: Lista de procedimentos identificados
        
    Returns:
        Boolean indicando se os procedimentos tratam a mesma doença
    """
    processador = ProcessadorProcedimentos()
    return processador.verificar_mesma_doenca(procedimentos)