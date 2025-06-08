"""
Módulo para download e processamento de documentos ZIP do PNCP
Responsável por baixar, extrair, identificar e organizar documentos de licitações
"""

import os
import requests
import zipfile
import tempfile
import shutil
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

# Configurar logging
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Classe principal para processamento de documentos do PNCP"""
    
    def __init__(self, db_connection):
        self.conn = db_connection
        self.storage_path = Path('./storage/documents')
        self.temp_path = Path('./storage/temp')
        
        # Criar diretórios se não existirem
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)
        
        # Padrões para identificar editais
        self.edital_patterns = [
            'edital', 'pregao', 'tomada_preco', 'concorrencia',
            'aviso', 'chamada', 'tr'
        ]
        
        # Extensões de arquivos aceitas
        self.allowed_extensions = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'}
    
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
                logger.info(f"🔍 Parâmetros: id={licitacao_id}, pncp_id={licitacao_id}")
                
                cursor.execute(query, (licitacao_id, licitacao_id))
                result = cursor.fetchone()
                
                if result:
                    logger.info(f"✅ Licitação encontrada: PNCP_ID={result.get('pncp_id')}")
                    logger.info(f"📊 CNPJ={result.get('orgao_cnpj')}, Ano={result.get('ano_compra')}, Seq={result.get('sequencial_compra')}")
                    return dict(result)
                else:
                    logger.error(f"❌ Licitação NÃO encontrada no banco para ID: {licitacao_id}")
                    
                    # Vamos verificar se existe alguma licitação com ID similar
                    cursor.execute("SELECT COUNT(*) FROM licitacoes")
                    total_licitacoes = cursor.fetchone()[0]
                    logger.info(f"📊 Total de licitações no banco: {total_licitacoes}")
                    
                    # Verificar se o ID está no formato correto
                    logger.info(f"🔍 Formato do ID recebido: {type(licitacao_id)} - '{licitacao_id}'")
                    
                    return None
                
        except Exception as e:
            logger.error(f"❌ ERRO na consulta da licitação {licitacao_id}: {e}")
            logger.error(f"🔍 Stack trace:", exc_info=True)
            return None
    
    def construir_url_documentos(self, licitacao_info: Dict) -> str:
        """Constrói URL da API do PNCP para baixar documentos"""
        try:
            cnpj = licitacao_info['orgao_cnpj']
            ano = licitacao_info['ano_compra']
            sequencial = licitacao_info['sequencial_compra']
            
            logger.info(f"🔧 Construindo URL com: CNPJ={cnpj}, Ano={ano}, Sequencial={sequencial}")
            
            # URL da API do PNCP para arquivos
            url = f"https://pncp.gov.br/pncp-api/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/arquivos"
            logger.info(f"✅ URL construída: {url}")
            return url
        except KeyError as e:
            logger.error(f"❌ ERRO: Campo obrigatório ausente na licitação: {e}")
            logger.error(f"📊 Campos disponíveis: {list(licitacao_info.keys())}")
            raise
        except Exception as e:
            logger.error(f"❌ ERRO ao construir URL: {e}")
            raise
    
    def baixar_documentos_pncp(self, url: str, licitacao_id: str) -> Optional[List[Dict]]:
        """Baixa documentos do PNCP (primeiro lista, depois baixa cada arquivo)"""
        try:
            logger.info(f"🌐 Buscando lista de documentos de: {url}")
            logger.info(f"📋 Licitação ID: {licitacao_id}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, application/zip, */*'
            }
            
            logger.info(f"📤 Headers da requisição: {headers}")
            
            # 1. Buscar lista de documentos
            logger.info(f"🔄 Fazendo requisição GET para: {url}")
            print(f"🌐 URL COMPLETA: {url}")  # Print para garantir que aparece no console
            
            response = requests.get(url, headers=headers, timeout=60)
            
            logger.info(f"📥 Status da resposta: {response.status_code}")
            logger.info(f"📄 Content-Type: {response.headers.get('content-type', 'não informado')}")
            logger.info(f"📊 Tamanho da resposta: {len(response.content)} bytes")
            
            response.raise_for_status()
            
            # Log do conteúdo da resposta (primeiros 500 caracteres)
            response_preview = response.text[:500] if hasattr(response, 'text') else str(response.content[:500])
            logger.info(f"📝 Preview da resposta: {response_preview}")
            
            print(f"📄 RESPOSTA JSON: {response.json()}")  # Print para garantir que aparece
            
            # 2. Verificar se é JSON (lista de documentos)
            content_type = response.headers.get('content-type', '')
            logger.info(f"🔍 Verificando content-type: {content_type}")
            
            if not content_type.startswith('application/json'):
                logger.warning(f"⚠️ Conteúdo não é JSON: {content_type}")
                return None
                
            documentos_lista = response.json()
            
            if not isinstance(documentos_lista, list) or len(documentos_lista) == 0:
                logger.warning("Nenhum documento encontrado na resposta da API")
                return None
                
            logger.info(f"Encontrados {len(documentos_lista)} documentos para download")
            
            # 3. Baixar cada documento individualmente
            documentos_baixados = []
            
            for i, doc_info in enumerate(documentos_lista):
                try:
                    doc_url = doc_info.get('url') or doc_info.get('uri')
                    doc_titulo = doc_info.get('titulo', f'documento_{i+1}')
                    doc_tipo = doc_info.get('tipoDocumentoNome', 'Desconhecido')
                    
                    if not doc_url:
                        logger.warning(f"URL não encontrada para documento: {doc_titulo}")
                        continue
                        
                    logger.info(f"Baixando documento {i+1}/{len(documentos_lista)}: {doc_titulo}")
                    
                    # Baixar o arquivo específico
                    doc_response = requests.get(doc_url, headers=headers, timeout=120)
                    doc_response.raise_for_status()
                    
                    # Verificar se é realmente um arquivo (não JSON de erro)
                    content_type = doc_response.headers.get('content-type', '')
                    if content_type.startswith('application/json'):
                        logger.warning(f"Documento {doc_titulo} retornou JSON ao invés de arquivo")
                        continue
                        
                    # Determinar extensão do arquivo
                    if doc_titulo.endswith('.pdf'):
                        extensao = '.pdf'
                    elif 'pdf' in content_type.lower():
                        extensao = '.pdf'
                    else:
                        # Tentar detectar pelo magic
                        try:
                            tipo_arquivo = magic.from_buffer(doc_response.content[:1024], mime=True)
                            if 'pdf' in tipo_arquivo:
                                extensao = '.pdf'
                            elif 'word' in tipo_arquivo or 'document' in tipo_arquivo:
                                extensao = '.docx'
                            else:
                                extensao = '.bin'
                        except:
                            extensao = '.bin'
                    
                    # Garantir que o título tenha a extensão correta
                    if not doc_titulo.endswith(extensao):
                        doc_titulo = f"{doc_titulo.split('.')[0]}{extensao}"
                    
                    # Salvar arquivo
                    nome_arquivo = f"{licitacao_id}_{i+1}_{doc_titulo}"
                    caminho_arquivo = self.storage_path / nome_arquivo
                    
                    with open(caminho_arquivo, 'wb') as f:
                        f.write(doc_response.content)
                    
                    logger.info(f"Documento salvo: {caminho_arquivo} ({len(doc_response.content)} bytes)")
                    
                    # Criar entrada do documento
                    documento = {
                        'licitacao_id': licitacao_id,
                        'titulo': doc_titulo,
                        'nome_arquivo': doc_titulo,
                        'arquivo_local': str(caminho_arquivo),
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
                            'classificacao_automatica': 'edital_principal' if self._e_edital_principal(doc_titulo, doc_tipo) else 'anexo'
                        }
                    }
                    
                    documentos_baixados.append(documento)
                    
                except Exception as e:
                    logger.error(f"Erro ao baixar documento {i+1} ({doc_info.get('titulo', 'sem título')}): {e}")
                    continue
            
            logger.info(f"Download concluído: {len(documentos_baixados)} documentos baixados com sucesso")
            return documentos_baixados if documentos_baixados else None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de rede ao buscar documentos: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao processar documentos: {e}")
            return None
    
    def _limpar_nome_arquivo(self, nome: str) -> str:
        """Remove caracteres problemáticos do nome do arquivo"""
        import re
        # Remove caracteres não alfanuméricos (exceto . - _)
        nome_limpo = re.sub(r'[^\w\-_\.]', '_', nome)
        # Remove underscores múltiplos
        nome_limpo = re.sub(r'_+', '_', nome_limpo)
        return nome_limpo.strip('_')
    
    def _calcular_hash_conteudo(self, conteudo: bytes) -> str:
        """Calcula hash SHA-256 do conteúdo"""
        return hashlib.sha256(conteudo).hexdigest()
    
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
    
    def _processar_zip_direto(self, response, licitacao_id: str) -> Optional[List[Dict]]:
        """Método obsoleto - mantido apenas para compatibilidade"""
        logger.warning("Método _processar_zip_direto está obsoleto")
        return None
    
    def extrair_e_classificar_documentos(self, zip_path: str, licitacao_id: str) -> List[Dict]:
        """Extrai arquivos do ZIP e classifica como edital ou anexo"""
        try:
            documentos_extraidos = []
            extract_dir = self.temp_path / f"extracted_{licitacao_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            extract_dir.mkdir(exist_ok=True)
            
            logger.info(f"Extraindo ZIP para: {extract_dir}")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extrair todos os arquivos
                zip_ref.extractall(extract_dir)
                
                # Percorrer todos os arquivos extraídos recursivamente
                for file_path in extract_dir.rglob('*'):
                    if file_path.is_file():
                        # Verificar extensão
                        if file_path.suffix.lower() not in self.allowed_extensions:
                            logger.debug(f"Arquivo ignorado (extensão): {file_path}")
                            continue
                        
                        # Verificar se não é arquivo temporário/sistema
                        if file_path.name.startswith('.') or '__MACOSX' in str(file_path):
                            continue
                        
                        # Classificar documento
                        doc_info = self._classificar_documento(file_path, licitacao_id)
                        if doc_info:
                            documentos_extraidos.append(doc_info)
            
            logger.info(f"Extraídos {len(documentos_extraidos)} documentos válidos")
            return documentos_extraidos
            
        except zipfile.BadZipFile:
            logger.error(f"Arquivo ZIP corrompido: {zip_path}")
            return []
        except Exception as e:
            logger.error(f"Erro ao extrair documentos: {e}")
            return []
        finally:
            # Limpar diretório temporário
            if 'extract_dir' in locals() and extract_dir.exists():
                shutil.rmtree(extract_dir, ignore_errors=True)
    
    def _classificar_documento(self, file_path: Path, licitacao_id: str) -> Optional[Dict]:
        """Classifica um documento como edital principal ou anexo"""
        try:
            # Informações básicas do arquivo
            file_name = file_path.name.lower()
            file_size = file_path.stat().st_size
            
            # Calcular hash do arquivo
            file_hash = self._calcular_hash_arquivo(file_path)
            
            # Detectar tipo de arquivo
            try:
                mime_type = magic.from_file(str(file_path), mime=True)
            except:
                mime_type = 'application/octet-stream'
            
            # Classificar como edital ou anexo baseado no nome
            is_edital_principal = any(pattern in file_name for pattern in self.edital_patterns)
            
            # Se contém "anexo" no nome, é anexo mesmo que tenha padrão de edital
            if 'anexo' in file_name or 'anexo_' in file_name:
                is_edital_principal = False
            
            # Copiar arquivo para storage permanente
            storage_subdir = self.storage_path / licitacao_id
            storage_subdir.mkdir(exist_ok=True)
            
            # Gerar nome único para evitar conflitos
            unique_filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_path.name}"
            dest_path = storage_subdir / unique_filename
            
            shutil.copy2(file_path, dest_path)
            
            # Extrair texto se for PDF (para metadata)
            texto_preview = self._extrair_texto_preview(dest_path) if file_path.suffix.lower() == '.pdf' else None
            
            documento_info = {
                'licitacao_id': licitacao_id,
                'titulo': file_path.stem,  # Nome sem extensão
                'nome_arquivo': file_path.name,
                'arquivo_local': str(dest_path),
                'tamanho_arquivo': file_size,
                'tipo_arquivo': mime_type,
                'hash_arquivo': file_hash,
                'is_edital_principal': is_edital_principal,
                'texto_preview': texto_preview,
                'metadata_arquivo': {
                    'nome_original': file_path.name,
                    'caminho_no_zip': str(file_path.relative_to(file_path.parents[2])),  # Caminho relativo no ZIP
                    'extensao': file_path.suffix.lower(),
                    'classificacao_automatica': 'edital_principal' if is_edital_principal else 'anexo'
                }
            }
            
            return documento_info
            
        except Exception as e:
            logger.error(f"Erro ao classificar documento {file_path}: {e}")
            return None
    
    def _calcular_hash_arquivo(self, file_path: Path) -> str:
        """Calcula hash SHA-256 do arquivo"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Erro ao calcular hash: {e}")
            return ""
    
    def _extrair_texto_preview(self, file_path: Path, max_chars: int = 500) -> Optional[str]:
        """Extrai preview do texto de um PDF"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                
                # Extrair texto das primeiras páginas
                for i, page in enumerate(reader.pages[:3]):  # Máximo 3 páginas
                    text += page.extract_text() + "\n"
                    if len(text) > max_chars:
                        break
                
                return text[:max_chars].strip() if text.strip() else None
                
        except Exception as e:
            logger.debug(f"Erro ao extrair texto preview de {file_path}: {e}")
            return None
    
    def salvar_documentos_no_banco(self, documentos: List[Dict]) -> Dict[str, Any]:
        """Salva informações dos documentos no banco de dados"""
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
                        # Salvar como anexo (precisa do edital_id)
                        anexos_salvos.append(doc)
                
                # Salvar anexos (vincular ao primeiro edital encontrado ou criar edital genérico)
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
            logger.error(f"Erro ao salvar documentos no banco: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _salvar_edital(self, cursor, doc_info: Dict) -> Optional[str]:
        """Salva edital principal no banco"""
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
                doc_info['arquivo_local'],
                'edital_principal',
                doc_info['tamanho_arquivo'],
                doc_info['hash_arquivo'],
                'processado',
                json.dumps(doc_info['metadata_arquivo'])  # Converter para JSON
            ))
            
            logger.info(f"Edital salvo: {edital_id}")
            return edital_id
            
        except Exception as e:
            logger.error(f"Erro ao salvar edital: {e}")
            return None
    
    def _salvar_anexo(self, cursor, doc_info: Dict, edital_id: str) -> Optional[str]:
        """Salva anexo no banco"""
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
                doc_info['arquivo_local'],
                doc_info['tamanho_arquivo'],
                doc_info['hash_arquivo'],
                'processado',
                json.dumps(doc_info['metadata_arquivo'])  # Converter para JSON
            ))
            
            logger.info(f"Anexo salvo: {anexo_id}")
            return anexo_id
            
        except Exception as e:
            logger.error(f"Erro ao salvar anexo: {e}")
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
                json.dumps({'tipo': 'edital_generico', 'criado_automaticamente': True})  # Converter para JSON
            ))
            
            logger.info(f"Edital genérico criado: {edital_id}")
            return edital_id
            
        except Exception as e:
            logger.error(f"Erro ao criar edital genérico: {e}")
            return str(uuid.uuid4())  # Fallback
    
    def processar_documentos_licitacao(self, licitacao_id: str) -> Dict[str, Any]:
        """Função principal: processa todos os documentos de uma licitação"""
        try:
            logger.info(f"🚀 INICIANDO processamento de documentos para licitação: {licitacao_id}")
            
            # 1. Extrair informações da licitação
            logger.info(f"📋 PASSO 1: Extraindo informações da licitação...")
            licitacao_info = self.extrair_info_licitacao(licitacao_id)
            
            if not licitacao_info:
                logger.error(f"❌ ERRO PASSO 1: Licitação não encontrada no banco: {licitacao_id}")
                return {
                    'success': False,
                    'error': 'Licitação não encontrada'
                }
            
            logger.info(f"✅ PASSO 1 OK: Licitação encontrada - {licitacao_info.get('pncp_id', 'ID desconhecido')}")
            logger.info(f"📊 Dados da licitação: CNPJ={licitacao_info.get('orgao_cnpj')}, Ano={licitacao_info.get('ano_compra')}, Seq={licitacao_info.get('sequencial_compra')}")
            
            # 2. Verificar se documentos já foram processados
            logger.info(f"📋 PASSO 2: Verificando se documentos já existem...")
            if self._documentos_ja_existem(licitacao_id):
                logger.info(f"✅ DOCUMENTOS JÁ EXISTEM: Retornando documentos existentes")
                return {
                    'success': True,
                    'message': 'Documentos já foram processados anteriormente',
                    'documentos_existentes': True
                }
            
            logger.info(f"✅ PASSO 2 OK: Nenhum documento existente, prosseguindo...")
            
            # 3. Construir URL e baixar documentos
            logger.info(f"📋 PASSO 3: Construindo URL da API PNCP...")
            url_documentos = self.construir_url_documentos(licitacao_info)
            logger.info(f"🌐 URL construída: {url_documentos}")
            
            logger.info(f"📋 PASSO 4: Baixando documentos do PNCP...")
            documentos = self.baixar_documentos_pncp(url_documentos, licitacao_id)
            
            if not documentos:
                logger.warning("⚠️ PASSO 4 FALHOU: Não foi possível baixar documentos do PNCP")
                logger.info("🔄 Tentando criar documento virtual...")
                documentos = self.criar_documento_fallback(licitacao_info)
                
                if not documentos:
                    logger.error("❌ FALLBACK FALHOU: Não foi possível criar documento virtual")
                    return {
                        'success': False,
                        'error': 'Falha ao baixar documentos do PNCP e ao criar documento virtual'
                    }
                else:
                    logger.info(f"✅ FALLBACK OK: Documento virtual criado")
            else:
                logger.info(f"✅ PASSO 4 OK: {len(documentos)} documentos baixados com sucesso")
            
            try:
                # 4. Processar texto dos PDFs se necessário
                logger.info(f"📋 PASSO 5: Processando texto dos PDFs...")
                for i, doc in enumerate(documentos):
                    if doc['arquivo_local'].endswith('.pdf') and doc['texto_preview'] is None:
                        logger.info(f"📄 Extraindo texto do PDF {i+1}: {doc.get('titulo', 'sem título')}")
                        doc['texto_preview'] = self._extrair_texto_preview(Path(doc['arquivo_local']))
                
                logger.info(f"✅ PASSO 5 OK: Texto extraído de todos os PDFs")
                
                # 5. Salvar no banco de dados
                logger.info(f"📋 PASSO 6: Salvando documentos no banco de dados...")
                resultado_salvamento = self.salvar_documentos_no_banco(documentos)
                
                if resultado_salvamento['success']:
                    logger.info(f"✅ PASSO 6 OK: {resultado_salvamento['total_documentos']} documentos salvos no banco")
                    logger.info(f"📊 Resultado final: {resultado_salvamento['editais_salvos']} editais, {resultado_salvamento['anexos_salvos']} anexos")
                    return {
                        'success': True,
                        'message': f"Processamento concluído com sucesso",
                        'licitacao_id': licitacao_id,
                        'documentos_processados': resultado_salvamento['total_documentos'],
                        'editais_encontrados': resultado_salvamento['editais_salvos'],
                        'anexos_encontrados': resultado_salvamento['anexos_salvos'],
                        'documentos': resultado_salvamento['documentos']
                    }
                else:
                    logger.error(f"❌ PASSO 6 FALHOU: Erro ao salvar no banco: {resultado_salvamento.get('error', 'Erro desconhecido')}")
                    return resultado_salvamento
                    
            finally:
                # Nota: Arquivos ficam no storage permanente, não limpar
                pass
            
        except Exception as e:
            logger.error(f"❌ ERRO GERAL no processamento de documentos: {e}")
            logger.error(f"🔍 Stack trace:", exc_info=True)
            return {
                'success': False,
                'error': f'Erro no processamento: {str(e)}'
            }
    
    def _documentos_ja_existem(self, licitacao_id: str) -> bool:
        """Verifica se documentos da licitação já foram processados"""
        try:
            logger.info(f"🔍 Verificando se documentos já existem para licitação: {licitacao_id}")
            
            with self.conn.cursor() as cursor:
                query = "SELECT COUNT(*) FROM editais WHERE licitacao_id = %s"
                logger.info(f"🔍 Query de verificação: {query}")
                
                cursor.execute(query, (licitacao_id,))
                count = cursor.fetchone()[0]
                
                logger.info(f"📊 Documentos encontrados no banco: {count}")
                
                exists = count > 0
                if exists:
                    logger.info(f"✅ Documentos JÁ EXISTEM para esta licitação")
                else:
                    logger.info(f"📝 Nenhum documento existente, prosseguir com download")
                    
                return exists
                
        except Exception as e:
            logger.error(f"❌ ERRO ao verificar documentos existentes: {e}")
            logger.error(f"🔍 Stack trace:", exc_info=True)
            return False
    
    def obter_documentos_licitacao(self, licitacao_id: str) -> List[Dict]:
        """Obtém documentos já processados de uma licitação"""
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
                    
                    # Buscar anexos deste edital
                    cursor.execute("""
                        SELECT * FROM edital_anexos WHERE edital_id = %s
                    """, (edital['id'],))
                    anexos = cursor.fetchall()
                    
                    edital_dict['anexos'] = [dict(anexo) for anexo in anexos]
                    documentos.append(edital_dict)
                
                return documentos
                
        except Exception as e:
            logger.error(f"Erro ao obter documentos da licitação: {e}")
            return []
    
    def criar_documento_fallback(self, licitacao_info: Dict) -> List[Dict]:
        """Cria documento virtual baseado nos dados da licitação quando não há arquivos"""
        try:
            logger.info(f"🔄 Criando documento virtual baseado nos dados da licitação")
            logger.info(f"📊 Dados disponíveis: {list(licitacao_info.keys())}")
            
            # Criar conteúdo baseado nos dados da licitação
            orgao_info = licitacao_info.get('orgao_entidade', {})
            if isinstance(orgao_info, str):
                orgao_nome = orgao_info
            else:
                orgao_nome = orgao_info.get('razaoSocial', 'Não informado') if orgao_info else 'Não informado'
            
            conteudo_virtual = f"""
LICITAÇÃO - DADOS BÁSICOS

ÓRGÃO: {orgao_nome}
CNPJ: {licitacao_info.get('orgao_cnpj', 'Não informado')}
UF: {licitacao_info.get('uf', 'Não informado')}

DADOS DA LICITAÇÃO:
Número: {licitacao_info.get('sequencial_compra', 'Não informado')}
Ano: {licitacao_info.get('ano_compra', 'Não informado')}
PNCP ID: {licitacao_info.get('pncp_id', 'Não informado')}
Modalidade: {licitacao_info.get('modalidade_nome', 'Não informado')}

OBJETO DA COMPRA:
{licitacao_info.get('objeto_compra', 'Não informado')}

VALORES:
Valor Total Estimado: R$ {licitacao_info.get('valor_total_estimado', 0):,.2f}

DATAS:
Data de Publicação: {licitacao_info.get('data_publicacao', 'Não informado')}
Data de Abertura: {licitacao_info.get('data_abertura_proposta', 'Não informado')}
Data de Encerramento: {licitacao_info.get('data_encerramento_proposta', 'Não informado')}

STATUS: {licitacao_info.get('status', 'Não informado')}

OBSERVAÇÃO: Este documento foi gerado automaticamente a partir dos dados disponíveis na API do PNCP, 
pois não foi possível baixar os documentos oficiais da licitação.
            """.strip()
            
            logger.info(f"📝 Conteúdo virtual criado: {len(conteudo_virtual)} caracteres")
            
            # Salvar arquivo virtual
            storage_subdir = self.storage_path / licitacao_info['id']
            storage_subdir.mkdir(exist_ok=True)
            
            nome_arquivo = f"dados_licitacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            arquivo_path = storage_subdir / nome_arquivo
            
            logger.info(f"💾 Salvando arquivo virtual em: {arquivo_path}")
            
            with open(arquivo_path, 'w', encoding='utf-8') as f:
                f.write(conteudo_virtual)
            
            documento_virtual = {
                'licitacao_id': licitacao_info['id'],
                'titulo': 'Dados da Licitação (Gerado Automaticamente)',
                'nome_arquivo': nome_arquivo,
                'arquivo_local': str(arquivo_path),
                'tamanho_arquivo': len(conteudo_virtual.encode('utf-8')),
                'tipo_arquivo': 'text/plain',
                'hash_arquivo': hashlib.sha256(conteudo_virtual.encode('utf-8')).hexdigest(),
                'is_edital_principal': True,  # Considerar como edital principal
                'texto_preview': conteudo_virtual[:500],
                'metadata_arquivo': {
                    'nome_original': nome_arquivo,
                    'tipo_origem': 'documento_virtual',
                    'fonte': 'api_pncp',
                    'extensao': '.txt',
                    'gerado_automaticamente': True
                }
            }
            
            logger.info(f"✅ Documento virtual criado com sucesso")
            logger.info(f"📊 Tamanho: {documento_virtual['tamanho_arquivo']} bytes")
            
            return [documento_virtual]
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar documento virtual: {e}")
            logger.error(f"🔍 Stack trace:", exc_info=True)
            return []

def cleanup_temp_files():
    """Função utilitária para limpar arquivos temporários antigos"""
    try:
        temp_path = Path('./storage/temp')
        if temp_path.exists():
            import time
            current_time = time.time()
            
            for file_path in temp_path.iterdir():
                # Deletar arquivos com mais de 1 hora
                if current_time - file_path.stat().st_mtime > 3600:
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        shutil.rmtree(file_path, ignore_errors=True)
                        
            logger.info("Limpeza de arquivos temporários concluída")
            
    except Exception as e:
        logger.error(f"Erro na limpeza de arquivos temporários: {e}") 