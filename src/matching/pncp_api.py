#!/usr/bin/env python3
"""
Módulo para integração com API do PNCP e operações de banco de dados
"""

import os
import psycopg2
from psycopg2.extras import DictCursor
import datetime
from typing import List, Dict, Any, Tuple
import requests
import time
import json
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# --- Configurações da API PNCP ---
PNCP_BASE_URL_PUBLICACAO = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
PNCP_BASE_URL_ITENS = "https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{anoCompra}/{sequencialCompra}/itens"
PNCP_PAGE_SIZE = 50  # Quantidade de licitações por página
PNCP_MAX_PAGES = 5   # Limite de páginas por UF para evitar sobrecarga

# --- Estados brasileiros ---
ESTADOS_BRASIL = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO"
]


def get_db_connection():
    """Conecta ao banco Supabase usando DATABASE_URL"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL não encontrada nas variáveis de ambiente")
    
    return psycopg2.connect(database_url)


def get_all_companies_from_db() -> List[Dict[str, Any]]:
    """Busca todas as empresas do banco de dados"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("""
                SELECT id, nome_fantasia, razao_social, cnpj, 
                       descricao_servicos_produtos, palavras_chave, setor_atuacao
                FROM empresas
                ORDER BY nome_fantasia
            """)
            companies = []
            for row in cursor.fetchall():
                companies.append({
                    'id': str(row['id']),
                    'nome': row['nome_fantasia'],
                    'razao_social': row['razao_social'],
                    'cnpj': row['cnpj'],
                    'descricao_servicos_produtos': row['descricao_servicos_produtos'],
                    'palavras_chave': row['palavras_chave'],
                    'setor_atuacao': row['setor_atuacao']
                })
            return companies
    finally:
        conn.close()


def get_processed_bid_ids() -> set:
    """Retorna conjunto de IDs de licitações já processadas"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT pncp_id FROM licitacoes")
            return {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()


def fetch_bids_from_pncp(start_date: str, end_date: str, uf: str, page: int) -> Tuple[List[Dict], bool]:
    """
    Busca licitações na API do PNCP para um UF e página específicos.
    Retorna a lista de licitações e um booleano indicando se há mais páginas.
    """
    params = {
        "dataInicial": start_date,
        "dataFinal": end_date,
        "uf": uf,
        "pagina": page,
        "quantidade": PNCP_PAGE_SIZE,
        "codigoModalidadeContratacao": 6  # Pregão eletrônico
    }
    
    try:
        print(f"🔍 Buscando licitações em {uf}, página {page}...")
        response = requests.get(PNCP_BASE_URL_PUBLICACAO, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        bids = data.get("data", [])
        has_more_pages = len(bids) == PNCP_PAGE_SIZE
        print(f"   ✅ Encontradas {len(bids)} licitações em {uf}")
        return bids, has_more_pages
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao buscar licitações do PNCP ({uf}, página {page}): {e}")
        return [], False


def fetch_bid_items_from_pncp(licitacao: Dict) -> List[Dict]:
    """
    Busca os itens detalhados de uma licitação específica.
    """
    orgao_cnpj = licitacao["orgaoEntidade"]["cnpj"]
    ano_compra = licitacao["anoCompra"]
    sequencial_compra = licitacao["sequencialCompra"]

    url = PNCP_BASE_URL_ITENS.format(
        cnpj=orgao_cnpj,
        anoCompra=ano_compra,
        sequencialCompra=sequencial_compra
    )
    
    try:
        print(f"   📋 Buscando itens para licitação {licitacao['numeroControlePNCP']}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        items = response.json()
        print(f"      ✅ {len(items)} itens encontrados")
        return items
    except requests.exceptions.RequestException as e:
        print(f"      ❌ Erro ao buscar itens da licitação {licitacao['numeroControlePNCP']}: {e}")
        return []


def save_bid_to_db(bid: Dict) -> str:
    """Salva uma licitação no banco de dados e retorna o ID"""
    # Validar e limitar valor total estimado
    valor_total = bid.get("valorTotalEstimado")
    if valor_total is not None:
        try:
            valor_total = float(valor_total)
            # Limitar a 999 bilhões (limite do DECIMAL(15,2))
            if valor_total > 999999999999.99:
                valor_total = 999999999999.99
            elif valor_total < 0:
                valor_total = 0
        except (ValueError, TypeError):
            valor_total = None
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO licitacoes (
                    pncp_id, orgao_cnpj, ano_compra, sequencial_compra,
                    objeto_compra, link_sistema_origem, data_publicacao,
                    valor_total_estimado, uf, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (pncp_id) DO UPDATE SET
                    updated_at = NOW()
                RETURNING id
            """, (
                bid["numeroControlePNCP"],
                bid["orgaoEntidade"]["cnpj"],
                bid["anoCompra"],
                bid["sequencialCompra"],
                bid["objetoCompra"],
                bid.get("linkSistemaOrigem", ""),
                bid.get("dataPublicacao"),
                valor_total,
                bid.get("ufSigla"),
                "coletada"
            ))
            result = cursor.fetchone()
            conn.commit()
            return str(result[0])
    finally:
        conn.close()


def save_bid_items_to_db(licitacao_id: str, items: List[Dict]):
    """Salva os itens de uma licitação no banco"""
    if not items:
        return
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            for i, item in enumerate(items, 1):
                # Validar e limitar valor unitário estimado
                valor_unitario = item.get("valorUnitarioEstimado", 0)
                try:
                    valor_unitario = float(valor_unitario) if valor_unitario is not None else 0
                    # Limitar a 999 bilhões (limite do DECIMAL(15,2))
                    if valor_unitario > 999999999999.99:
                        valor_unitario = 999999999999.99
                    elif valor_unitario < 0:
                        valor_unitario = 0
                except (ValueError, TypeError):
                    valor_unitario = 0
                
                # Validar quantidade
                quantidade = item.get("quantidade", 0)
                try:
                    quantidade = float(quantidade) if quantidade is not None else 0
                    if quantidade < 0:
                        quantidade = 0
                except (ValueError, TypeError):
                    quantidade = 0
                
                cursor.execute("""
                    INSERT INTO licitacao_itens (
                        licitacao_id, numero_item, descricao, quantidade,
                        unidade_medida, valor_unitario_estimado
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (licitacao_id, numero_item) DO NOTHING
                """, (
                    licitacao_id,
                    item.get("numeroItem", i),
                    item.get("descricao", ""),
                    quantidade,
                    item.get("unidadeMedida", ""),
                    valor_unitario
                ))
            conn.commit()
    finally:
        conn.close()


def save_match_to_db(licitacao_id: str, empresa_id: str, score: float, match_type: str, justificativa: str = ""):
    """Salva um match no banco de dados"""
    # Converter score para float Python nativo se for numpy
    if hasattr(score, 'item'):
        score = float(score.item())
    else:
        score = float(score)
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO matches (
                    licitacao_id, empresa_id, score_similaridade, 
                    match_type, justificativa_match
                ) VALUES (
                    (SELECT id FROM licitacoes WHERE pncp_id = %s), 
                    %s, %s, %s, %s
                )
            """, (licitacao_id, empresa_id, score, match_type, justificativa))
            conn.commit()
            print(f"      ✅ Match salvo: Score {score:.3f} - {match_type}")
            if justificativa:
                print(f"         💡 Justificativa: {justificativa}")
    finally:
        conn.close()


def update_bid_status(pncp_id: str, status: str):
    """Atualiza o status de uma licitação"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE licitacoes 
                SET status = %s, updated_at = NOW() 
                WHERE pncp_id = %s
            """, (status, pncp_id))
            conn.commit()
    finally:
        conn.close()


def get_existing_bids_from_db() -> List[Dict[str, Any]]:
    """Busca todas as licitações já armazenadas no banco de dados"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    l.id, l.pncp_id, l.objeto_compra, l.uf, l.valor_total_estimado,
                    l.data_publicacao, l.status, l.created_at
                FROM licitacoes l
                ORDER BY l.created_at DESC
            """)
            bids = []
            for row in cursor.fetchall():
                bids.append({
                    'id': str(row['id']),
                    'pncp_id': row['pncp_id'],
                    'objeto_compra': row['objeto_compra'],
                    'uf': row['uf'],
                    'valor_total_estimado': row['valor_total_estimado'],
                    'data_publicacao': row['data_publicacao'],
                    'status': row['status'],
                    'created_at': row['created_at']
                })
            return bids
    finally:
        conn.close()


def get_bid_items_from_db(licitacao_id: str) -> List[Dict[str, Any]]:
    """Busca os itens de uma licitação específica do banco"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("""
                SELECT numero_item, descricao, quantidade, unidade_medida, valor_unitario_estimado
                FROM licitacao_itens
                WHERE licitacao_id = %s
                ORDER BY numero_item
            """, (licitacao_id,))
            items = []
            for row in cursor.fetchall():
                items.append({
                    'numeroItem': row['numero_item'],
                    'descricao': row['descricao'],
                    'quantidade': row['quantidade'],
                    'unidadeMedida': row['unidade_medida'],
                    'valorUnitarioEstimado': row['valor_unitario_estimado']
                })
            return items
    finally:
        conn.close()


def clear_existing_matches():
    """Remove todos os matches existentes para permitir reavaliação"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM matches")
            conn.commit()
            print("🗑️  Matches anteriores limpos do banco")
    finally:
        conn.close() 