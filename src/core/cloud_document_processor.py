"""
Módulo para download e processamento de documentos usando Supabase Storage
Responsável por baixar, extrair, identificar e organizar documentos de licitações na nuvem
"""

import os
import requests
import tempfile
import hashlib
import magic
import logging
import uuid
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from urllib.parse import urlparse
import psycopg2
from psycopg2.extras import DictCursor
import PyPDF2
import io
from datetime import datetime
from supabase import create_client, Client

# Configurar logging
logger = logging.getLogger(__name__)

class CloudDocumentProcessor:
    """Classe para processamento de documentos usando Supabase Storage"""
    
    def __init__(self, db_connection):
        self.conn = db_connection
        
        # Configuração do Supabase
        self.supabase_url = "https://hdlowzlkwrboqfzjewom.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhkbG93emxrd3Jib3Fmempld29tIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc0MTU4NjMsImV4cCI6MjA2Mjk5MTg2M30._h-0Oq1mudUcC1KVIV03yuZOI2PVbugwLxCW1rXgU44"
        
        # Inicializar cliente Supabase
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Nome do bucket para documentos
        self.bucket_name = "licitacao-documents"
        
        # Criar diretório temporário local (apenas para processamento)
        self.temp_path = Path('./storage/temp')
        self.temp_path.mkdir(parents=True, exist_ok=True)
        
        # Padrões para identificar editais
        self.edital_patterns = [
            'edital', 'pregao', 'tomada_preco', 'concorrencia',
            'aviso', 'chamada', 'tr'
        ]
        
        # Extensões de arquivos aceitas
        self.allowed_extensions = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'}
        
        # Garantir que o bucket existe
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Garante que o bucket para documentos existe"""
        try:
            # Tentar listar buckets para verificar se existe
            buckets = self.supabase.storage.list_buckets()
            
            bucket_exists = any(bucket.name == self.bucket_name for bucket in buckets)
            
            if not bucket_exists:
                logger.info(f"📦 Criando bucket: {self.bucket_name}")
                # Criar bucket apenas com o nome (configuração mínima)
                result = self.supabase.storage.create_bucket(self.bucket_name)
                logger.info(f"✅ Bucket criado: {result}")
            else:
                logger.info(f"✅ Bucket já existe: {self.bucket_name}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao verificar/criar bucket: {e}")
            # Se falhar, apenas logar o erro e continuar
            logger.warning(f"⚠️ Prosseguindo sem verificação do bucket. Bucket pode já existir.")
    
    def _upload_to_supabase(self, file_content: bytes, file_path: str, content_type: str = None) -> Optional[str]:
        """Upload de arquivo para o Supabase Storage"""
        try:
            logger.info(f"☁️ Fazendo upload para: {file_path}")
            
            # Fazer upload com configurações mais simples
            file_options = {}
            if content_type:
                file_options["contentType"] = content_type
            
            result = self.supabase.storage.from_(self.bucket_name).upload(
                file_path, 
                file_content,
                file_options=file_options
            )
            
            # O resultado do Supabase Storage pode ser diferente, vamos verificar
            logger.info(f"📤 Resultado do upload: {result}")
            
            # Se chegou até aqui sem erro, assumir sucesso
            logger.info(f"✅ Upload concluído: {file_path}")
            
            try:
                # Tentar gerar URL pública (para debug)
                public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(file_path)
                logger.info(f"🔗 URL do arquivo: {public_url}")
            except Exception as url_error:
                logger.warning(f"⚠️ Não foi possível gerar URL pública: {url_error}")
            
            return file_path
                
        except Exception as e:
            logger.error(f"❌ Erro no upload para Supabase: {e}")
            logger.error(f"🔍 Detalhes do erro: {type(e).__name__}: {str(e)}")
            return None
    
    def _download_from_supabase(self, file_path: str) -> Optional[bytes]:
        """Download de arquivo do Supabase Storage"""
        try:
            logger.info(f"☁️ Baixando de: {file_path}")
            
            result = self.supabase.storage.from_(self.bucket_name).download(file_path)
            
            if result:
                logger.info(f"✅ Download concluído: {len(result)} bytes")
                return result
            else:
                logger.error(f"❌ Arquivo não encontrado: {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro no download do Supabase: {e}")
            return None
    
    def extrair_info_licitacao(self, licitacao_id: str) -> Optional[Dict]:
        """Extrai informações da licitação do banco de dados"""
        try:
            logger.info(f"🔍 Buscando licitação no banco: {licitacao_id}")
            
            with self.conn.cursor(cursor_factory=DictCursor) as cursor:
                query = """
                    SELECT id, pncp_id, orgao_cnpj, ano_compra, sequencial_compra, 
                           objeto_compra, status, modalidade_nome, modalidade_id,
                           valor_total_estimado, uf, data_publicacao, data_abertura_proposta,
                           data_encerramento_proposta, orgao_entidade, unidade_orgao
                    FROM licitacoes 
                    WHERE id = %s OR pncp_id = %s
                """
                
                logger.info(f"🔍 Executando query: {query}")
                cursor.execute(query, (licitacao_id, licitacao_id))
                result = cursor.fetchone()
                
                if result:
                    logger.info(f"✅ Licitação encontrada: PNCP_ID={result.get('pncp_id')}")
                    return dict(result)
                else:
                    logger.error(f"❌ Licitação NÃO encontrada: {licitacao_id}")
                    return None
                
        except Exception as e:
            logger.error(f"❌ ERRO na consulta da licitação: {e}")
            return None
    
    def construir_url_documentos(self, licitacao_info: Dict) -> str:
        """Constrói URL da API do PNCP para baixar documentos"""
        try:
            cnpj = licitacao_info['orgao_cnpj']
            ano = licitacao_info['ano_compra']
            sequencial = licitacao_info['sequencial_compra']
            
            url = f"https://pncp.gov.br/pncp-api/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/arquivos"
            logger.info(f"✅ URL construída: {url}")
            return url
        except KeyError as e:
            logger.error(f"❌ Campo obrigatório ausente: {e}")
            raise
    
    def baixar_documentos_pncp(self, url: str, licitacao_id: str) -> Optional[List[Dict]]:
        """Baixa documentos do PNCP e salva no Supabase Storage"""
        try:
            logger.info(f"🌐 Buscando lista de documentos de: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, application/zip, */*'
            }
            
            # 1. Buscar lista de documentos
            response = requests.get(url, headers=headers, timeout=60)
            response.raise_for_status()
            
            if not response.headers.get('content-type', '').startswith('application/json'):
                logger.warning("⚠️ Resposta não é JSON")
                return None
                
            documentos_lista = response.json()
            
            if not isinstance(documentos_lista, list) or len(documentos_lista) == 0:
                logger.warning("⚠️ Nenhum documento encontrado")
                return None
                
            logger.info(f"📄 Encontrados {len(documentos_lista)} documentos para download")
            
            # 2. Baixar cada documento e salvar no Supabase
            documentos_baixados = []
            
            for i, doc_info in enumerate(documentos_lista):
                try:
                    doc_url = doc_info.get('url') or doc_info.get('uri')
                    doc_titulo = doc_info.get('titulo', f'documento_{i+1}')
                    doc_tipo = doc_info.get('tipoDocumentoNome', 'Desconhecido')
                    
                    if not doc_url:
                        logger.warning(f"⚠️ URL não encontrada para: {doc_titulo}")
                        continue
                        
                    logger.info(f"📥 Baixando documento {i+1}/{len(documentos_lista)}: {doc_titulo}")
                    
                    # Baixar o arquivo
                    doc_response = requests.get(doc_url, headers=headers, timeout=120)
                    doc_response.raise_for_status()
                    
                    # Verificar se é arquivo válido
                    content_type = doc_response.headers.get('content-type', '')
                    if content_type.startswith('application/json'):
                        logger.warning(f"⚠️ Documento retornou JSON: {doc_titulo}")
                        continue
                    
                    # Determinar extensão
                    if doc_titulo.endswith('.pdf') or 'pdf' in content_type.lower():
                        extensao = '.pdf'
                    elif 'word' in content_type.lower() or 'document' in content_type.lower():
                        extensao = '.docx'
                    else:
                        try:
                            tipo_arquivo = magic.from_buffer(doc_response.content[:1024], mime=True)
                            if 'pdf' in tipo_arquivo:
                                extensao = '.pdf'
                            elif 'word' in tipo_arquivo or 'document' in tipo_arquivo:
                                extensao = '.docx'
                            else:
                                extensao = '.bin'
                        except:
                            extensao = '.pdf'  # Assumir PDF como padrão
                    
                    # Limpar nome do arquivo
                    nome_limpo = self._limpar_nome_arquivo(doc_titulo)
                    if not nome_limpo.endswith(extensao):
                        nome_limpo = f"{nome_limpo.split('.')[0]}{extensao}"
                    
                    # Caminho no Supabase Storage
                    cloud_path = f"licitacoes/{licitacao_id}/{i+1}_{nome_limpo}"
                    
                    # Upload para Supabase
                    upload_path = self._upload_to_supabase(
                        doc_response.content, 
                        cloud_path, 
                        content_type or 'application/pdf'
                    )
                    
                    if upload_path:
                        logger.info(f"☁️ Documento salvo na nuvem: {upload_path}")
                        
                        # Criar entrada do documento
                        documento = {
                            'licitacao_id': licitacao_id,
                            'titulo': doc_titulo,
                            'nome_arquivo': nome_limpo,
                            'arquivo_nuvem': upload_path,  # Caminho na nuvem
                            'tamanho_arquivo': len(doc_response.content),
                            'tipo_arquivo': content_type or 'application/pdf',
                            'hash_arquivo': hashlib.sha256(doc_response.content).hexdigest(),
                            'is_edital_principal': self._e_edital_principal(doc_titulo, doc_tipo),
                            'texto_preview': None,
                            'metadata_arquivo': {
                                'sequencial_documento': doc_info.get('sequencialDocumento'),
                                'data_publicacao': doc_info.get('dataPublicacaoPncp'),
                                'tipo_documento_id': doc_info.get('tipoDocumentoId'),
                                'status_ativo': doc_info.get('statusAtivo', True),
                                'nome_original': doc_titulo,
                                'tipo_documento_nome': doc_tipo,
                                'fonte': 'PNCP',
                                'url_origem': doc_url,
                                'extensao': extensao,
                                'storage_provider': 'supabase',
                                'bucket_name': self.bucket_name,
                                'classificacao_automatica': 'edital_principal' if self._e_edital_principal(doc_titulo, doc_tipo) else 'anexo'
                            }
                        }
                        
                        # Extrair texto se for PDF
                        if extensao == '.pdf':
                            documento['texto_preview'] = self._extrair_texto_preview_from_bytes(doc_response.content)
                        
                        documentos_baixados.append(documento)
                    else:
                        logger.error(f"❌ Falha no upload: {doc_titulo}")
                        
                except Exception as e:
                    logger.error(f"❌ Erro ao processar documento {i+1}: {e}")
                    continue
            
            logger.info(f"✅ Download concluído: {len(documentos_baixados)} documentos salvos na nuvem")
            return documentos_baixados if documentos_baixados else None
            
        except Exception as e:
            logger.error(f"❌ Erro no download dos documentos: {e}")
            return None
    
    def _limpar_nome_arquivo(self, nome: str) -> str:
        """Remove caracteres problemáticos do nome do arquivo"""
        import re
        # Remove caracteres não alfanuméricos (exceto . - _)
        nome_limpo = re.sub(r'[^\w\-_\.]', '_', nome)
        # Remove underscores múltiplos
        nome_limpo = re.sub(r'_+', '_', nome_limpo)
        return nome_limpo.strip('_')
    
    def _e_edital_principal(self, titulo: str, tipo_doc: str) -> bool:
        """Determina se é um edital principal baseado no título e tipo"""
        titulo_lower = titulo.lower()
        tipo_lower = tipo_doc.lower()
        
        # Se o tipo do PNCP indica que é edital
        if 'edital' in tipo_lower:
            return True
        
        # Se contém "anexo" no nome, não é edital principal
        if 'anexo' in titulo_lower:
            return False
        
        # Verificar padrões no título
        padroes_edital = ['edital', 'pregao', 'tomada_preco', 'concorrencia', 'tr']
        return any(padrao in titulo_lower for padrao in padroes_edital)
    
    def _extrair_texto_preview_from_bytes(self, pdf_bytes: bytes, max_chars: int = 500) -> Optional[str]:
        """Extrai preview do texto de um PDF a partir dos bytes"""
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            
            # Extrair texto das primeiras páginas
            for i, page in enumerate(reader.pages[:3]):  # Máximo 3 páginas
                text += page.extract_text() + "\n"
                if len(text) > max_chars:
                    break
            
            return text[:max_chars].strip() if text.strip() else None
            
        except Exception as e:
            logger.debug(f"⚠️ Erro ao extrair texto do PDF: {e}")
            return None
    
    def salvar_documentos_no_banco(self, documentos: List[Dict]) -> Dict[str, Any]:
        """Salva informações dos documentos no banco de dados (com referências na nuvem)"""
        try:
            documentos_salvos = []
            anexos_salvos = []
            
            with self.conn.cursor(cursor_factory=DictCursor) as cursor:
                for doc in documentos:
                    if doc['is_edital_principal']:
                        # Salvar como edital principal
                        edital_id = self._salvar_edital(cursor, doc)
                        if edital_id:
                            doc['edital_id'] = edital_id
                            documentos_salvos.append(doc)
                    else:
                        # Salvar como anexo
                        anexos_salvos.append(doc)
                
                # Salvar anexos
                if anexos_salvos:
                    edital_id = documentos_salvos[0]['edital_id'] if documentos_salvos else self._criar_edital_generico(cursor, anexos_salvos[0]['licitacao_id'])
                    
                    for anexo in anexos_salvos:
                        anexo_id = self._salvar_anexo(cursor, anexo, edital_id)
                        if anexo_id:
                            anexo['anexo_id'] = anexo_id
                
                self.conn.commit()
            
            return {
                'success': True,
                'editais_salvos': len(documentos_salvos),
                'anexos_salvos': len(anexos_salvos),
                'total_documentos': len(documentos),
                'documentos': documentos_salvos + anexos_salvos
            }
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro ao salvar documentos no banco: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _salvar_edital(self, cursor, doc_info: Dict) -> Optional[str]:
        """Salva edital principal no banco (com referência na nuvem)"""
        try:
            edital_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO editais (
                    id, licitacao_id, titulo, arquivo_local, 
                    tipo_documento, tamanho_arquivo, hash_arquivo,
                    status_processamento, metadata_extracao
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                edital_id,
                doc_info['licitacao_id'],
                doc_info['titulo'],
                doc_info['arquivo_nuvem'],  # Caminho na nuvem ao invés de local
                'edital_principal',
                doc_info['tamanho_arquivo'],
                doc_info['hash_arquivo'],
                'processado',
                json.dumps(doc_info['metadata_arquivo'])
            ))
            
            logger.info(f"☁️ Edital salvo (nuvem): {edital_id}")
            return edital_id
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar edital: {e}")
            return None
    
    def _salvar_anexo(self, cursor, doc_info: Dict, edital_id: str) -> Optional[str]:
        """Salva anexo no banco (com referência na nuvem)"""
        try:
            anexo_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO edital_anexos (
                    id, edital_id, titulo, arquivo_local,
                    tamanho_arquivo, hash_arquivo,
                    status_processamento, metadata_arquivo
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                anexo_id,
                edital_id,
                doc_info['titulo'],
                doc_info['arquivo_nuvem'],  # Caminho na nuvem
                doc_info['tamanho_arquivo'],
                doc_info['hash_arquivo'],
                'processado',
                json.dumps(doc_info['metadata_arquivo'])
            ))
            
            logger.info(f"☁️ Anexo salvo (nuvem): {anexo_id}")
            return anexo_id
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar anexo: {e}")
            return None
    
    def _criar_edital_generico(self, cursor, licitacao_id: str) -> str:
        """Cria um edital genérico quando só há anexos"""
        try:
            edital_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO editais (
                    id, licitacao_id, titulo, tipo_documento,
                    status_processamento, metadata_extracao
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                edital_id,
                licitacao_id,
                'Documentos da Licitação (Genérico)',
                'documento_agrupador',
                'processado',
                json.dumps({'tipo': 'edital_generico', 'criado_automaticamente': True, 'storage_provider': 'supabase'})
            ))
            
            logger.info(f"📋 Edital genérico criado: {edital_id}")
            return edital_id
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar edital genérico: {e}")
            return str(uuid.uuid4())
    
    def _documentos_ja_existem(self, licitacao_id: str) -> bool:
        """Verifica se documentos da licitação já foram processados"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM editais WHERE licitacao_id = %s", (licitacao_id,))
                count = cursor.fetchone()[0]
                return count > 0
        except Exception as e:
            logger.error(f"❌ Erro ao verificar documentos existentes: {e}")
            return False
    
    def processar_documentos_licitacao(self, licitacao_id: str) -> Dict[str, Any]:
        """Função principal: processa todos os documentos de uma licitação usando nuvem"""
        try:
            logger.info(f"☁️ INICIANDO processamento com Supabase Storage: {licitacao_id}")
            
            # 1. Extrair informações da licitação
            licitacao_info = self.extrair_info_licitacao(licitacao_id)
            if not licitacao_info:
                return {'success': False, 'error': 'Licitação não encontrada'}
            
            # 2. Verificar se documentos já existem
            if self._documentos_ja_existem(licitacao_id):
                logger.info(f"✅ Documentos já existem na nuvem")
                return {
                    'success': True,
                    'message': 'Documentos já foram processados anteriormente',
                    'documentos_existentes': True
                }
            
            # 3. Baixar documentos e salvar na nuvem
            url_documentos = self.construir_url_documentos(licitacao_info)
            documentos = self.baixar_documentos_pncp(url_documentos, licitacao_id)
            
            if not documentos:
                logger.warning("⚠️ Não foi possível baixar documentos do PNCP")
                return {
                    'success': False,
                    'error': 'Falha ao baixar documentos do PNCP'
                }
            
            # 4. Salvar no banco de dados
            resultado_salvamento = self.salvar_documentos_no_banco(documentos)
            
            if resultado_salvamento['success']:
                logger.info(f"✅ Processamento na nuvem concluído com sucesso!")
                return {
                    'success': True,
                    'message': f"Processamento concluído - documentos na nuvem",
                    'licitacao_id': licitacao_id,
                    'documentos_processados': resultado_salvamento['total_documentos'],
                    'editais_encontrados': resultado_salvamento['editais_salvos'],
                    'anexos_encontrados': resultado_salvamento['anexos_salvos'],
                    'storage_provider': 'supabase',
                    'documentos': resultado_salvamento['documentos']
                }
            else:
                return resultado_salvamento
                
        except Exception as e:
            logger.error(f"❌ ERRO no processamento na nuvem: {e}")
            return {
                'success': False,
                'error': f'Erro no processamento: {str(e)}'
            }
    
    def baixar_documento_da_nuvem(self, cloud_path: str) -> Optional[bytes]:
        """Baixa um documento específico da nuvem"""
        return self._download_from_supabase(cloud_path)
    
    def obter_documentos_licitacao(self, licitacao_id: str) -> List[Dict]:
        """Obtém documentos já processados de uma licitação (referências na nuvem)"""
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cursor:
                # Buscar editais
                cursor.execute("""
                    SELECT * FROM editais WHERE licitacao_id = %s
                """, (licitacao_id,))
                editais = cursor.fetchall()
                
                documentos = []
                for edital in editais:
                    edital_dict = dict(edital)
                    edital_dict['tipo'] = 'edital'
                    edital_dict['storage_provider'] = 'supabase'
                    
                    # Buscar anexos deste edital
                    cursor.execute("""
                        SELECT * FROM edital_anexos WHERE edital_id = %s
                    """, (edital['id'],))
                    anexos = cursor.fetchall()
                    
                    edital_dict['anexos'] = [dict(anexo) for anexo in anexos]
                    documentos.append(edital_dict)
                
                return documentos
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter documentos da licitação: {e}")
            return [] 