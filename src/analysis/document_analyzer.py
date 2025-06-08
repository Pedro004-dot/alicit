"""
Módulo principal para análise de editais e documentos de licitação
Responsável pela orquestração do processo de análise de documentos e geração de contexto
"""

import os
import logging
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncio
from dataclasses import dataclass
import json
import PyPDF2
from io import BytesIO
import tempfile
import psycopg2
from psycopg2.extras import DictCursor

from .ai_services import EmbeddingGenerator, ChecklistGenerator
from .checklist_manager import ChecklistManager
from core import DocumentProcessor

# Configurar logging
logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """Representa um chunk de documento para processamento RAG"""
    texto: str
    ordem: int
    metadata: Dict
    embedding: Optional[List[float]] = None

class DocumentAnalyzer:
    """Classe principal para análise de editais com RAG"""
    
    def __init__(self, db_connection):
        self.conn = db_connection
        self.document_processor = DocumentProcessor(db_connection)
        self.embedding_generator = EmbeddingGenerator()
        self.checklist_generator = ChecklistGenerator()
        self.checklist_manager = ChecklistManager(db_connection)
    
    async def analisar_licitacao(self, licitacao_id: str) -> Dict[str, Any]:
        """
        Analisa licitação completa e gera checklist com IA
        
        Args:
            licitacao_id: ID da licitação a ser analisada
            
        Returns:
            Dict com resultado da análise, incluindo sucesso/erro, checklist_id, dados do checklist
        """
        try:
            logger.info(f"Iniciando análise da licitação: {licitacao_id}")
            
            # 1. Processar documentos (download + extração) se necessário
            resultado_docs = self.document_processor.processar_documentos_licitacao(licitacao_id)
            
            if not resultado_docs['success']:
                return resultado_docs
            
            # 2. Obter documentos processados do banco de dados
            documentos = self._obter_documentos_processados(licitacao_id)
            
            if not documentos:
                return {
                    'success': False,
                    'error': 'Nenhum documento processado encontrado'
                }
            
            # 3. Extrair contexto completo dos documentos
            contexto_completo = await self._extrair_contexto_documentos(documentos)
            
            if not contexto_completo or len(contexto_completo.strip()) == 0:
                return {
                    'success': False,
                    'error': 'Nenhum texto foi extraído dos documentos'
                }
            
            # 4. Gerar checklist usando IA
            licitacao_info = self.document_processor.extrair_info_licitacao(licitacao_id)
            objeto_licitacao = licitacao_info.get('objeto_compra', '') if licitacao_info else ''
            
            checklist_data = await self.checklist_generator.gerar_checklist(
                contexto_completo, objeto_licitacao
            )
            
            # 5. Salvar checklist no banco através do ChecklistManager
            checklist_id = self.checklist_manager.salvar_checklist(licitacao_id, checklist_data)
            
            return {
                'success': True,
                'message': 'Análise concluída com sucesso',
                'licitacao_id': licitacao_id,
                'checklist_id': checklist_id,
                'documentos_processados': len(documentos),
                'checklist': checklist_data
            }
            
        except Exception as e:
            logger.error(f"Erro na análise da licitação: {e}")
            await self.checklist_manager.marcar_erro_checklist(licitacao_id, str(e))
            return {
                'success': False,
                'error': f'Erro na análise: {str(e)}'
            }
    
    async def _extrair_contexto_documentos(self, documentos: List[Dict]) -> str:
        """
        Extrai texto consolidado de todos os documentos
        
        Args:
            documentos: Lista de documentos com metadados
            
        Returns:
            String com o contexto completo extraído
        """
        try:
            logger.info(f"🔄 Extraindo contexto de {len(documentos)} documentos")
            
            # Extrair texto de todos os documentos
            texto_completo = self._extrair_texto_documentos(documentos)
            
            if not texto_completo:
                logger.error("❌ Nenhum texto foi extraído dos documentos")
                return ""
            
            # Limitar tamanho do contexto (máximo ~15k caracteres para o prompt)
            if len(texto_completo) > 15000:
                texto_completo = texto_completo[:15000] + "\n...[TEXTO TRUNCADO]"
            
            logger.info(f"✅ Contexto extraído: {len(texto_completo)} caracteres")
            return texto_completo
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair contexto: {e}")
            return ""
    
    def _obter_documentos_processados(self, licitacao_id: str) -> List[Dict]:
        """
        Obtém documentos já processados do banco de dados
        
        Args:
            licitacao_id: ID da licitação
            
        Returns:
            Lista de documentos processados com metadados
        """
        try:
            from psycopg2.extras import RealDictCursor
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, titulo, arquivo_local, tipo_documento, status_processamento
                    FROM editais 
                    WHERE licitacao_id = %s AND status_processamento = 'processado'
                    ORDER BY created_at ASC
                """, (licitacao_id,))
                
                documentos = cursor.fetchall()
                logger.info(f"Encontrados {len(documentos)} documentos processados para análise")
                
                return [dict(doc) for doc in documentos]
                
        except Exception as e:
            logger.error(f"Erro ao obter documentos processados: {e}")
            return []

    def _extrair_texto_documentos(self, documentos: List[Dict]) -> str:
        """
        Extrai texto completo de todos os documentos de uma licitação
        Suporta arquivos locais e na nuvem (Supabase Storage)
        
        Args:
            documentos: Lista de documentos com metadados
            
        Returns:
            String com todo o texto extraído concatenado
        """
        texto_completo = ""
        
        logger.info(f"📄 Extraindo texto de {len(documentos)} documentos")
        
        for doc in documentos:
            try:
                arquivo_path = doc.get('arquivo_local', '')
                doc_titulo = doc.get('titulo', 'Documento sem título')
                
                logger.info(f"📖 Processando documento: {doc_titulo}")
                
                # Verificar se é um arquivo na nuvem (contém licitacoes/ no path)
                if 'licitacoes/' in arquivo_path:
                    texto_doc = self._extrair_texto_documento_nuvem(arquivo_path, doc_titulo)
                elif os.path.exists(arquivo_path):
                    texto_doc = self._extrair_texto_documento_local(arquivo_path)
                else:
                    logger.warning(f"⚠️ Arquivo não encontrado: {arquivo_path}")
                    texto_doc = f"Arquivo não encontrado: {doc_titulo}"
                
                if texto_doc and texto_doc.strip():
                    texto_completo += f"\n\n=== {doc_titulo} ===\n{texto_doc}\n"
                    logger.info(f"✅ Texto extraído: {len(texto_doc)} caracteres")
                else:
                    logger.warning(f"⚠️ Nenhum texto extraído de: {doc_titulo}")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao extrair texto do documento {doc.get('titulo', 'desconhecido')}: {e}")
                continue
        
        if not texto_completo.strip():
            logger.error("❌ Nenhum texto foi extraído de nenhum documento")
            return ""
        
        logger.info(f"✅ Extração concluída: {len(texto_completo)} caracteres totais")
        return texto_completo
    
    def _extrair_texto_documento_nuvem(self, arquivo_path: str, doc_titulo: str) -> str:
        """
        Extrai texto de documento armazenado na nuvem (Supabase Storage)
        
        Args:
            arquivo_path: Caminho do arquivo na nuvem
            doc_titulo: Título do documento para logs
            
        Returns:
            Texto extraído do documento
        """
        try:
            logger.info(f"☁️ Documento na nuvem detectado: {arquivo_path}")
            
            # Processar documentos da nuvem se disponíveis
            logger.info("📄 Buscando documentos na nuvem...")
            try:
                from core import CloudDocumentProcessor
            except ImportError:
                logger.warning("Não foi possível importar CloudDocumentProcessor do módulo core")
                return f"Erro ao processar documento: {doc_titulo}"
            
            # Criar uma conexão temporária para download
            temp_conn = get_db_connection()
            cloud_processor = CloudDocumentProcessor(temp_conn)
            
            # Baixar o arquivo da nuvem
            file_content = cloud_processor.baixar_documento_da_nuvem(arquivo_path)
            
            if file_content:
                logger.info(f"✅ Arquivo baixado da nuvem: {len(file_content)} bytes")
                
                # Extrair texto do PDF baixado
                if arquivo_path.endswith('.pdf'):
                    texto_doc = self._extrair_texto_pdf_from_bytes(file_content)
                else:
                    texto_doc = f"Documento {doc_titulo} (tipo não suportado para extração)"
            else:
                logger.error(f"❌ Falha ao baixar documento da nuvem: {arquivo_path}")
                texto_doc = f"Erro ao baixar documento: {doc_titulo}"
            
            temp_conn.close()
            return texto_doc
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar documento na nuvem: {e}")
            return f"Erro no processamento: {doc_titulo}"
    
    def _extrair_texto_documento_local(self, arquivo_path: str) -> str:
        """
        Extrai texto de documento armazenado localmente
        
        Args:
            arquivo_path: Caminho do arquivo local
            
        Returns:
            Texto extraído do documento
        """
        try:
            logger.info(f"💾 Processando arquivo local: {arquivo_path}")
            
            if arquivo_path.endswith('.pdf'):
                return self._extrair_texto_pdf_local(arquivo_path)
            elif arquivo_path.endswith(('.txt', '.md')):
                with open(arquivo_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return f"Tipo de arquivo não suportado: {arquivo_path}"
                
        except Exception as e:
            logger.error(f"❌ Erro ao extrair texto do arquivo local {arquivo_path}: {e}")
            return f"Erro ao processar arquivo: {arquivo_path}"
    
    def _extrair_texto_pdf_from_bytes(self, pdf_bytes: bytes) -> str:
        """
        Extrai texto de um PDF a partir dos bytes (para arquivos na nuvem)
        
        Args:
            pdf_bytes: Conteúdo do PDF em bytes
            
        Returns:
            Texto extraído do PDF
        """
        try:
            import io
            import PyPDF2
            
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n\n--- Página {page_num + 1} ---\n{page_text}"
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao extrair texto da página {page_num + 1}: {e}")
                    continue
            
            return text.strip() if text.strip() else None
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair texto do PDF (bytes): {e}")
            return None
    
    def _extrair_texto_pdf_local(self, caminho_arquivo: str) -> Optional[str]:
        """
        Extrai texto de um arquivo PDF local
        
        Args:
            caminho_arquivo: Caminho para o arquivo PDF
            
        Returns:
            Texto extraído do PDF ou None se falhar
        """
        try:
            import PyPDF2
            
            with open(caminho_arquivo, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text_parts = []
                
                # Extrair texto de todas as páginas
                for page in reader.pages:
                    text_parts.append(page.extract_text())
                
                return "\n".join(text_parts)
                
        except Exception as e:
            logger.error(f"Erro ao extrair texto de {caminho_arquivo}: {e}")
            return None

    def obter_checklist(self, licitacao_id: str) -> Optional[Dict]:
        """
        Obtém checklist existente da licitação
        
        Args:
            licitacao_id: ID da licitação
            
        Returns:
            Dados do checklist ou None se não existir
        """
        return self.checklist_manager.obter_checklist(licitacao_id)

# Importação condicional para evitar imports circulares quando usado no módulo matching
try:
    from matching import get_db_connection
except ImportError:
    logger.warning("Não foi possível importar get_db_connection do módulo matching") 