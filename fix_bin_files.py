#!/usr/bin/env python3
"""
Script para corrigir arquivos .bin que deveriam ser .pdf
e reprocessar documentos pendentes
"""

import os
import psycopg2
from psycopg2.extras import DictCursor
import magic
from pathlib import Path
import shutil

def get_db_connection():
    """Conecta ao banco Supabase usando config.env"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        # Carregar do config.env se não estiver nas env vars
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

def fix_bin_files():
    """Corrige arquivos .bin que deveriam ser .pdf"""
    conn = get_db_connection()
    
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            # Buscar editais com status pendente e arquivos .bin
            cursor.execute("""
                SELECT id, licitacao_id, titulo, arquivo_local, status_processamento
                FROM editais 
                WHERE status_processamento = 'pendente' 
                AND arquivo_local LIKE '%.bin'
            """)
            
            editais_bin = cursor.fetchall()
            
            print(f"Encontrados {len(editais_bin)} editais .bin pendentes")
            
            for edital in editais_bin:
                arquivo_bin = edital['arquivo_local']
                print(f"\nProcessando: {arquivo_bin}")
                
                if not os.path.exists(arquivo_bin):
                    print(f"Arquivo não encontrado: {arquivo_bin}")
                    continue
                
                # Verificar se é realmente um PDF
                try:
                    with open(arquivo_bin, 'rb') as f:
                        header = f.read(1024)
                        file_type = magic.from_buffer(header, mime=True)
                        
                    print(f"Tipo detectado: {file_type}")
                    
                    if 'pdf' in file_type.lower():
                        # Renomear para .pdf
                        arquivo_pdf = arquivo_bin.replace('.bin', '.pdf')
                        shutil.move(arquivo_bin, arquivo_pdf)
                        print(f"Arquivo renomeado: {arquivo_bin} -> {arquivo_pdf}")
                        
                        # Atualizar banco de dados
                        titulo_novo = edital['titulo'].replace('.bin', '.pdf')
                        
                        cursor.execute("""
                            UPDATE editais 
                            SET arquivo_local = %s, titulo = %s, status_processamento = 'processado'
                            WHERE id = %s
                        """, (arquivo_pdf, titulo_novo, edital['id']))
                        
                        print(f"Banco atualizado para: {titulo_novo}")
                        
                    else:
                        print(f"Arquivo não é PDF: {file_type}")
                        
                except Exception as e:
                    print(f"Erro ao processar {arquivo_bin}: {e}")
            
            conn.commit()
            print(f"\n✅ Processamento concluído!")
            
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    # Configurar variáveis de ambiente
    os.environ.setdefault('DATABASE_URL', 'postgresql://postgres.hdlowzlkwrboqfzjewom:WOxaFvYM6EzCGJmC@aws-0-sa-east-1.pooler.supabase.com:6543/postgres')
    
    fix_bin_files() 