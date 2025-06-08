#!/usr/bin/env python3
"""
Processador Melhorado de Documentos
Explora recursivamente ZIPs extraídos, identifica edital principal e organiza arquivos
"""

import os
import psycopg2
from psycopg2.extras import DictCursor
import zipfile
from pathlib import Path
import shutil
import uuid
import hashlib
import json
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple

def get_db_connection():
    """Conecta ao banco Supabase usando config.env"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        try:
            with open('config.env', 'r') as f:
                for line in f:
                    if line.startswith('DATABASE_URL='):
                        database_url = line.split('=', 1)[1].strip()
                        break
        except FileNotFoundError:
            raise ValueError("Arquivo config.env não encontrado")
    
    if not database_url:
        raise ValueError("DATABASE_URL não encontrada")
    
    return psycopg2.connect(database_url)

class ImprovedDocumentProcessor:
    """Processador melhorado de documentos com exploração recursiva"""
    
    def __init__(self):
        self.conn = get_db_connection()
        
        # Padrões para identificar tipos de documentos
        self.edital_patterns = [
            r'edital',
            r'pregao',
            r'concorrencia',
            r'licitacao'
        ]
        
        self.aviso_patterns = [
            r'aviso',
            r'publicacao'
        ]
        
        self.anexo_patterns = [
            r'anexo',
            r'termo.*referencia',
            r'planilha',
            r'projeto.*basico'
        ]
    
    def processar_licitacao_completa(self, licitacao_id: str) -> Dict:
        """Processa completamente todos os documentos de uma licitação"""
        try:
            print(f"🔍 Processando licitação: {licitacao_id}")
            
            # 1. Buscar arquivos .bin (ZIPs disfarçados) para esta licitação
            arquivos_bin = self._buscar_arquivos_bin(licitacao_id)
            
            if not arquivos_bin:
                return {
                    'success': False,
                    'message': 'Nenhum arquivo encontrado para processar'
                }
            
            # 2. Extrair e processar cada ZIP
            documentos_processados = []
            
            for arquivo_bin in arquivos_bin:
                docs = self._processar_arquivo_zip(licitacao_id, arquivo_bin)
                documentos_processados.extend(docs)
            
            # 3. Identificar e classificar documentos
            edital_principal, outros_docs = self._classificar_documentos(documentos_processados)
            
            # 4. Salvar no banco de dados
            self._salvar_documentos_banco(licitacao_id, edital_principal, outros_docs)
            
            return {
                'success': True,
                'message': f'Processados {len(documentos_processados)} documentos',
                'edital_principal': edital_principal['nome'] if edital_principal else None,
                'total_documentos': len(documentos_processados),
                'outros_documentos': len(outros_docs)
            }
            
        except Exception as e:
            print(f"❌ Erro ao processar licitação: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _buscar_arquivos_bin(self, licitacao_id: str) -> List[str]:
        """Busca arquivos .bin relacionados à licitação"""
        storage_dir = Path('./storage/documents')
        arquivos_bin = []
        
        # Procurar por arquivos que contenham o licitacao_id
        for arquivo in storage_dir.glob('*.bin'):
            if licitacao_id in arquivo.name:
                arquivos_bin.append(str(arquivo))
        
        print(f"📁 Encontrados {len(arquivos_bin)} arquivos ZIP para processar")
        return arquivos_bin
    
    def _processar_arquivo_zip(self, licitacao_id: str, caminho_zip: str) -> List[Dict]:
        """Processa um arquivo ZIP extraindo recursivamente todos os documentos"""
        try:
            print(f"📦 Processando ZIP: {Path(caminho_zip).name}")
            
            # Criar diretório de extração único
            extract_id = str(uuid.uuid4())
            extract_dir = Path(f'./storage/documents/extracted_{extract_id}')
            extract_dir.mkdir(exist_ok=True)
            
            # Extrair ZIP
            with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Buscar recursivamente todos os documentos
            documentos = []
            documentos.extend(self._buscar_documentos_recursivo(extract_dir, licitacao_id))
            
            print(f"✅ Extraídos {len(documentos)} documentos do ZIP")
            return documentos
            
        except Exception as e:
            print(f"❌ Erro ao processar ZIP {caminho_zip}: {e}")
            return []
    
    def _buscar_documentos_recursivo(self, diretorio: Path, licitacao_id: str) -> List[Dict]:
        """Busca recursivamente todos os documentos em um diretório"""
        documentos = []
        
        # Extensões de arquivo suportadas
        extensoes_suportadas = ['.pdf', '.doc', '.docx', '.txt']
        
        # Percorrer recursivamente
        for item in diretorio.rglob('*'):
            if item.is_file() and item.suffix.lower() in extensoes_suportadas:
                
                # Calcular hash do arquivo
                arquivo_hash = self._calcular_hash_arquivo(item)
                
                documento = {
                    'id': str(uuid.uuid4()),
                    'nome_original': item.name,
                    'nome_limpo': self._limpar_nome_arquivo(item.name),
                    'caminho_completo': str(item),
                    'caminho_relativo': str(item.relative_to(diretorio.parent)),
                    'extensao': item.suffix.lower(),
                    'tamanho': item.stat().st_size,
                    'hash_arquivo': arquivo_hash,
                    'licitacao_id': licitacao_id,
                    'tipo_identificado': self._identificar_tipo_documento(item.name),
                    'created_at': datetime.datetime.now()
                }
                
                documentos.append(documento)
                print(f"   📄 Encontrado: {documento['nome_limpo']} ({documento['tipo_identificado']})")
        
        return documentos
    
    def _limpar_nome_arquivo(self, nome: str) -> str:
        """Remove caracteres especiais e decodifica nomes de arquivo"""
        import urllib.parse
        
        # Decodificar URL encoding
        nome_limpo = urllib.parse.unquote(nome)
        
        # Remover caracteres especiais desnecessários
        nome_limpo = re.sub(r'[^\w\s\-_.]', ' ', nome_limpo)
        nome_limpo = re.sub(r'\s+', ' ', nome_limpo).strip()
        
        return nome_limpo
    
    def _identificar_tipo_documento(self, nome: str) -> str:
        """Identifica o tipo de documento baseado no nome"""
        nome_lower = nome.lower()
        
        # Verificar se é edital principal
        for pattern in self.edital_patterns:
            if re.search(pattern, nome_lower):
                return 'edital_principal'
        
        # Verificar se é aviso
        for pattern in self.aviso_patterns:
            if re.search(pattern, nome_lower):
                return 'aviso_licitacao'
        
        # Verificar se é anexo
        for pattern in self.anexo_patterns:
            if re.search(pattern, nome_lower):
                return 'anexo'
        
        return 'documento_geral'
    
    def _classificar_documentos(self, documentos: List[Dict]) -> Tuple[Optional[Dict], List[Dict]]:
        """Classifica documentos identificando o edital principal"""
        
        # Procurar edital principal
        editais_principais = [doc for doc in documentos if doc['tipo_identificado'] == 'edital_principal']
        
        edital_principal = None
        if editais_principais:
            # Se há múltiplos editais, escolher o maior
            edital_principal = max(editais_principais, key=lambda x: x['tamanho'])
        else:
            # Se não encontrou edital específico, escolher o maior PDF
            pdfs = [doc for doc in documentos if doc['extensao'] == '.pdf']
            if pdfs:
                edital_principal = max(pdfs, key=lambda x: x['tamanho'])
        
        # Outros documentos
        outros_docs = [doc for doc in documentos if doc != edital_principal]
        
        print(f"🎯 Edital principal: {edital_principal['nome_limpo'] if edital_principal else 'Não identificado'}")
        print(f"📋 Outros documentos: {len(outros_docs)}")
        
        return edital_principal, outros_docs
    
    def _calcular_hash_arquivo(self, caminho_arquivo: Path) -> str:
        """Calcula hash SHA256 do arquivo"""
        hash_sha256 = hashlib.sha256()
        with open(caminho_arquivo, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _salvar_documentos_banco(self, licitacao_id: str, edital_principal: Optional[Dict], outros_docs: List[Dict]):
        """Salva documentos no banco de dados"""
        try:
            with self.conn.cursor() as cursor:
                
                # Salvar edital principal
                if edital_principal:
                    cursor.execute("""
                        INSERT INTO editais (
                            id, licitacao_id, titulo, arquivo_local, tipo_documento, 
                            hash_arquivo, tamanho_arquivo, is_edital_principal, 
                            status_processamento, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (hash_arquivo) DO NOTHING
                    """, (
                        edital_principal['id'],
                        licitacao_id,
                        edital_principal['nome_limpo'],
                        edital_principal['caminho_completo'],
                        edital_principal['tipo_identificado'],
                        edital_principal['hash_arquivo'],
                        edital_principal['tamanho'],
                        True,
                        'processado',
                        edital_principal['created_at']
                    ))
                
                # Salvar outros documentos
                for doc in outros_docs:
                    cursor.execute("""
                        INSERT INTO editais (
                            id, licitacao_id, titulo, arquivo_local, tipo_documento, 
                            hash_arquivo, tamanho_arquivo, is_edital_principal, 
                            status_processamento, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (hash_arquivo) DO NOTHING
                    """, (
                        doc['id'],
                        licitacao_id,
                        doc['nome_limpo'],
                        doc['caminho_completo'],
                        doc['tipo_identificado'],
                        doc['hash_arquivo'],
                        doc['tamanho'],
                        False,
                        'processado',
                        doc['created_at']
                    ))
                
                self.conn.commit()
                print(f"✅ Documentos salvos no banco: 1 principal + {len(outros_docs)} outros")
                
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erro ao salvar documentos: {e}")
            raise

def main():
    """Função principal para testar"""
    processor = ImprovedDocumentProcessor()
    
    # Testar com a licitação atual
    licitacao_id = "244a6559-57fb-4769-b95e-db57dbcf6dad"
    resultado = processor.processar_licitacao_completa(licitacao_id)
    
    print("\n" + "="*50)
    print("📊 RESULTADO:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main() 