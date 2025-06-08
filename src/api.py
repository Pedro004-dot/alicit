from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import logging
import datetime
import os
import asyncio
from dotenv import load_dotenv
from matching import (
    MockTextVectorizer, 
    OpenAITextVectorizer,
    SentenceTransformersVectorizer,
    HybridTextVectorizer,
    process_daily_bids, 
    reevaluate_existing_bids,
    get_existing_bids_from_db,
    get_all_companies_from_db,
    get_db_connection
)
from analysis import DocumentAnalyzer
from core import DocumentProcessor
import psycopg2
from psycopg2.extras import DictCursor
import uuid

# Carregar variáveis de ambiente do config.env ANTES de qualquer outra coisa
load_dotenv('config.env')

app = Flask(__name__)
CORS(app)  # Permitir requisições do React

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Estado global para controlar execução
process_status = {
    'daily_bids': {'running': False, 'last_result': None},
    'reevaluate': {'running': False, 'last_result': None},
    'is_running': False,
    'last_run': None,
    'status': 'idle',
    'results': None
}

def create_vectorizer(vectorizer_type: str):
    """
    Cria o vetorizador baseado no tipo especificado
    """
    try:
        if vectorizer_type == 'hybrid':
            logger.info("🔥 Criando Sistema Híbrido...")
            return HybridTextVectorizer()
        elif vectorizer_type == 'openai':
            logger.info("🔥 Criando OpenAI Embeddings...")
            return OpenAITextVectorizer()
        elif vectorizer_type == 'sentence_transformers':
            logger.info("🔥 Criando SentenceTransformers...")
            return SentenceTransformersVectorizer()
        elif vectorizer_type == 'mock':
            logger.info("⚠️  Criando MockTextVectorizer...")
            return MockTextVectorizer()
        else:
            logger.warning(f"Tipo de vetorizador desconhecido: {vectorizer_type}. Usando híbrido...")
            return HybridTextVectorizer()
    except Exception as e:
        logger.error(f"Erro ao criar vetorizador {vectorizer_type}: {e}")
        logger.info("🔄 Tentando fallback para MockTextVectorizer...")
        return MockTextVectorizer()

def update_similarity_thresholds(config):
    """
    Atualiza os thresholds globalmente se fornecidos na configuração
    """
    import matching
    
    if 'similarity_threshold_phase1' in config:
        matching.SIMILARITY_THRESHOLD_PHASE1 = float(config['similarity_threshold_phase1'])
        logger.info(f"📊 Threshold Fase 1 atualizado: {matching.SIMILARITY_THRESHOLD_PHASE1}")
    
    if 'similarity_threshold_phase2' in config:
        matching.SIMILARITY_THRESHOLD_PHASE2 = float(config['similarity_threshold_phase2'])
        logger.info(f"📊 Threshold Fase 2 atualizado: {matching.SIMILARITY_THRESHOLD_PHASE2}")
    
    if 'max_pages' in config:
        matching.PNCP_MAX_PAGES = int(config['max_pages'])
        logger.info(f"📄 Máximo de páginas atualizado: {matching.PNCP_MAX_PAGES}")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verificação de saúde da API"""
    return jsonify({'status': 'OK', 'message': 'API funcionando corretamente'})

@app.route('/api/bids', methods=['GET'])
def get_bids():
    """Buscar todas as licitações do banco de dados"""
    try:
        logger.info("Buscando licitações do banco de dados...")
        bids = get_existing_bids_from_db()
        
        # Converter dados para o formato esperado pelo frontend
        formatted_bids = []
        for bid in bids:
            formatted_bids.append({
                'id': bid['id'],
                'pncp_id': bid['pncp_id'],
                'objeto_compra': bid['objeto_compra'],
                'valor_total_estimado': float(bid.get('valor_total_estimado', 0)) if bid.get('valor_total_estimado') else 0,
                'uf': bid.get('uf', ''),
                'status': bid.get('status', ''),
                'data_publicacao': bid.get('data_publicacao', ''),
                'modalidade_compra': 'Pregão Eletrônico'  # Valor padrão pois não está no BD
            })
        
        return jsonify({
            'success': True,
            'data': formatted_bids,
            'total': len(formatted_bids),
            'message': f'{len(formatted_bids)} licitações encontradas'
        })
    except Exception as e:
        logger.error(f"Erro ao buscar licitações: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao buscar licitações do banco'
        }), 500

@app.route('/api/companies', methods=['GET'])
def get_companies():
    """Buscar todas as empresas do banco de dados"""
    try:
        logger.info("Buscando empresas do banco de dados...")
        companies = get_all_companies_from_db()
        
        # Converter dados para o formato esperado pelo frontend
        formatted_companies = []
        for company in companies:
            formatted_companies.append({
                'id': company['id'],
                'nome_fantasia': company['nome'],
                'razao_social': company['razao_social'],
                'cnpj': company['cnpj'],
                'descricao_servicos_produtos': company['descricao_servicos_produtos'],
                'palavras_chave': company['palavras_chave'] if company['palavras_chave'] else [],
                'setor_atuacao': company.get('setor_atuacao', '')
            })
        
        return jsonify({
            'success': True,
            'data': formatted_companies,
            'total': len(formatted_companies),
            'message': f'{len(formatted_companies)} empresas encontradas'
        })
    except Exception as e:
        logger.error(f"Erro ao buscar empresas: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao buscar empresas do banco'
        }), 500

@app.route('/api/companies', methods=['POST'])
def create_company():
    """Criar uma nova empresa no banco de dados"""
    try:
        data = request.get_json()
        
        # Validar campos obrigatórios
        required_fields = ['nome_fantasia', 'razao_social', 'descricao_servicos_produtos']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Campo obrigatório ausente: {field}'
                }), 400
        
        logger.info(f"Criando nova empresa: {data.get('nome_fantasia')}")
        
        # Conectar ao banco PostgreSQL
        conn = get_db_connection()
        
        try:
            with conn.cursor() as cursor:
                # Converter palavras_chave para JSON se for array
                palavras_chave = data.get('palavras_chave')
                if isinstance(palavras_chave, list):
                    import json
                    palavras_chave = json.dumps(palavras_chave)
                
                cursor.execute("""
                    INSERT INTO empresas (
                        nome_fantasia, razao_social, cnpj, 
                        descricao_servicos_produtos, palavras_chave, setor_atuacao
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    data['nome_fantasia'],
                    data['razao_social'],
                    data.get('cnpj'),
                    data['descricao_servicos_produtos'],
                    palavras_chave,
                    data.get('setor_atuacao')
                ))
                
                company_id = cursor.fetchone()[0]
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Empresa criada com sucesso',
                    'data': {'id': str(company_id)}
                }), 201
                
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Erro ao criar empresa: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao criar empresa'
        }), 500

@app.route('/api/companies/<company_id>', methods=['PUT'])
def update_company(company_id):
    """Atualizar uma empresa existente"""
    try:
        data = request.get_json()
        
        # Validar campos obrigatórios
        required_fields = ['nome_fantasia', 'razao_social', 'descricao_servicos_produtos']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Campo obrigatório ausente: {field}'
                }), 400
        
        logger.info(f"Atualizando empresa ID: {company_id}")
        
        # Conectar ao banco PostgreSQL
        conn = get_db_connection()
        
        try:
            with conn.cursor() as cursor:
                # Verificar se a empresa existe
                cursor.execute("SELECT id FROM empresas WHERE id = %s", (company_id,))
                if not cursor.fetchone():
                    return jsonify({
                        'success': False,
                        'message': 'Empresa não encontrada'
                    }), 404
                
                # Converter palavras_chave para JSON se for array
                palavras_chave = data.get('palavras_chave')
                if isinstance(palavras_chave, list):
                    import json
                    palavras_chave = json.dumps(palavras_chave)
                
                # Atualizar empresa
                cursor.execute("""
                    UPDATE empresas SET 
                        nome_fantasia = %s,
                        razao_social = %s,
                        cnpj = %s,
                        descricao_servicos_produtos = %s,
                        palavras_chave = %s,
                        setor_atuacao = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (
                    data['nome_fantasia'],
                    data['razao_social'],
                    data.get('cnpj'),
                    data['descricao_servicos_produtos'],
                    palavras_chave,
                    data.get('setor_atuacao'),
                    company_id
                ))
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Empresa atualizada com sucesso'
                })
                
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Erro ao atualizar empresa: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao atualizar empresa'
        }), 500

@app.route('/api/companies/<company_id>', methods=['DELETE'])
def delete_company(company_id):
    """Deletar uma empresa do banco de dados"""
    try:
        logger.info(f"Deletando empresa ID: {company_id}")
        
        # Conectar ao banco PostgreSQL
        conn = get_db_connection()
        
        try:
            with conn.cursor() as cursor:
                # Verificar se a empresa existe
                cursor.execute("SELECT id FROM empresas WHERE id = %s", (company_id,))
                company = cursor.fetchone()
                
                if not company:
                    return jsonify({
                        'success': False,
                        'message': 'Empresa não encontrada'
                    }), 404
                
                # Primeiro, deletar os matches relacionados
                cursor.execute("DELETE FROM matches WHERE empresa_id = %s", (company_id,))
                deleted_matches = cursor.rowcount
                logger.info(f"Deletados {deleted_matches} matches da empresa")
                
                # Depois, deletar a empresa
                cursor.execute("DELETE FROM empresas WHERE id = %s", (company_id,))
                
                if cursor.rowcount == 0:
                    return jsonify({
                        'success': False,
                        'message': 'Falha ao deletar empresa'
                    }), 500
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Empresa deletada com sucesso',
                    'data': {
                        'deleted_matches': deleted_matches
                    }
                })
                
        except Exception as e:
            conn.rollback()
            raise e
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Erro ao deletar empresa: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao deletar empresa do banco'
        }), 500

@app.route('/api/matches', methods=['GET'])
def get_matches():
    """Buscar todos os matches entre empresas e licitações"""
    try:
        logger.info("Buscando matches do banco de dados...")
        
        # Conectar ao banco PostgreSQL
        conn = get_db_connection()
        
        try:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                # Query para buscar matches com informações da empresa e licitação
                query = """
                SELECT 
                    m.id,
                    m.empresa_id,
                    m.licitacao_id,
                    m.score_similaridade as score,
                    m.match_type as tipo_match,
                    m.data_match as timestamp,
                    e.nome_fantasia as empresa_nome,
                    e.razao_social as empresa_razao_social,
                    e.cnpj as empresa_cnpj,
                    e.setor_atuacao as empresa_setor,
                    l.pncp_id,
                    l.objeto_compra,
                    l.valor_total_estimado,
                    l.uf,
                    l.status as licitacao_status,
                    l.data_publicacao
                FROM matches m
                JOIN empresas e ON m.empresa_id = e.id
                JOIN licitacoes l ON m.licitacao_id = l.id
                ORDER BY m.score_similaridade DESC, m.data_match DESC
                """
                
                cursor.execute(query)
                rows = cursor.fetchall()
                
                matches = []
                for row in rows:
                    match = {
                        'id': str(row['id']),
                        'empresa_id': str(row['empresa_id']),
                        'licitacao_id': str(row['licitacao_id']),
                        'score': float(row['score']),
                        'tipo_match': row['tipo_match'],
                        'timestamp': str(row['timestamp']),
                        'empresa': {
                            'nome': row['empresa_nome'],
                            'razao_social': row['empresa_razao_social'],
                            'cnpj': row['empresa_cnpj'],
                            'setor_atuacao': row['empresa_setor'] or ''
                        },
                        'licitacao': {
                            'pncp_id': row['pncp_id'],
                            'objeto_compra': row['objeto_compra'],
                            'valor_total_estimado': float(row['valor_total_estimado']) if row['valor_total_estimado'] else 0,
                            'uf': row['uf'] or '',
                            'status': row['licitacao_status'],
                            'data_publicacao': str(row['data_publicacao']) if row['data_publicacao'] else '',
                            'modalidade_compra': 'Pregão Eletrônico'  # Valor padrão
                        }
                    }
                    matches.append(match)
                
                return jsonify({
                    'success': True,
                    'data': matches,
                    'total': len(matches),
                    'message': f'{len(matches)} matches encontrados'
                })
                
        finally:
            conn.close()
        
    except Exception as e:
        logger.error(f"Erro ao buscar matches: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao buscar matches do banco'
        }), 500

@app.route('/api/matches/by-company', methods=['GET'])
def get_matches_by_company():
    """Buscar matches agrupados por empresa"""
    try:
        logger.info("Buscando matches agrupados por empresa...")
        
        conn = get_db_connection()
        
        try:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                # Query para buscar matches agrupados por empresa
                query = """
                SELECT 
                    e.id as empresa_id,
                    e.nome_fantasia as empresa_nome,
                    e.razao_social,
                    e.cnpj,
                    e.setor_atuacao,
                    COUNT(m.id) as total_matches,
                    AVG(m.score_similaridade) as score_medio,
                    MAX(m.score_similaridade) as melhor_score,
                    MIN(m.score_similaridade) as pior_score
                FROM empresas e
                LEFT JOIN matches m ON e.id = m.empresa_id
                GROUP BY e.id, e.nome_fantasia, e.razao_social, e.cnpj, e.setor_atuacao
                HAVING COUNT(m.id) > 0
                ORDER BY COUNT(m.id) DESC, AVG(m.score_similaridade) DESC
                """
                
                cursor.execute(query)
                rows = cursor.fetchall()
                
                companies_matches = []
                for row in rows:
                    company_match = {
                        'empresa_id': str(row['empresa_id']),
                        'empresa_nome': row['empresa_nome'],
                        'razao_social': row['razao_social'],
                        'cnpj': row['cnpj'],
                        'setor_atuacao': row['setor_atuacao'] or '',
                        'total_matches': row['total_matches'],
                        'score_medio': round(float(row['score_medio']), 3) if row['score_medio'] else 0,
                        'melhor_score': round(float(row['melhor_score']), 3) if row['melhor_score'] else 0,
                        'pior_score': round(float(row['pior_score']), 3) if row['pior_score'] else 0
                    }
                    companies_matches.append(company_match)
                
                return jsonify({
                    'success': True,
                    'data': companies_matches,
                    'total': len(companies_matches),
                    'message': f'{len(companies_matches)} empresas com matches encontradas'
                })
                
        finally:
            conn.close()
        
    except Exception as e:
        logger.error(f"Erro ao buscar matches por empresa: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao buscar matches por empresa'
        }), 500

@app.route('/api/search-new-bids', methods=['POST'])
def search_new_bids():
    """Iniciar busca de novas licitações com configurações personalizadas"""
    if process_status['daily_bids']['running']:
        return jsonify({
            'success': False,
            'message': 'Processo de busca já está em execução'
        }), 400
    
    # Obter configurações do corpo da requisição
    config = request.get_json() or {}
    logger.info(f"📋 Configurações recebidas: {config}")
    
    def run_process():
        global process_status
        process_status['daily_bids']['running'] = True
        
        try:
            logger.info("🚀 Iniciando busca de novas licitações com configuração personalizada...")
            
            # Atualizar thresholds se fornecidos
            update_similarity_thresholds(config)
            
            # Criar vetorizador baseado na configuração
            vectorizer_type = config.get('vectorizer_type', 'hybrid')
            vectorizer = create_vectorizer(vectorizer_type)
            
            # Executar busca
            process_daily_bids(vectorizer)
            
            process_status['daily_bids']['last_result'] = {
                'success': True,
                'message': 'Busca de novas licitações concluída com sucesso',
                'timestamp': datetime.datetime.now().isoformat(),
                'config_used': config
            }
            logger.info("✅ Busca de novas licitações concluída!")
            
        except Exception as e:
            error_msg = f"Erro na busca de licitações: {str(e)}"
            logger.error(error_msg)
            process_status['daily_bids']['last_result'] = {
                'success': False,
                'message': error_msg,
                'timestamp': datetime.datetime.now().isoformat(),
                'error': str(e)
            }
        finally:
            process_status['daily_bids']['running'] = False
    
    # Executar em thread separada
    thread = threading.Thread(target=run_process)
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Busca de novas licitações iniciada em background',
        'config': config
    })

@app.route('/api/reevaluate-bids', methods=['POST'])
def reevaluate_bids():
    """Iniciar reavaliação de licitações existentes com configurações personalizadas"""
    if process_status['reevaluate']['running']:
        return jsonify({
            'success': False,
            'message': 'Processo de reavaliação já está em execução'
        }), 400
    
    # Obter configurações do corpo da requisição
    config = request.get_json() or {}
    logger.info(f"📋 Configurações recebidas: {config}")
    
    def run_process():
        global process_status
        process_status['reevaluate']['running'] = True
        
        try:
            logger.info("🔄 Iniciando reavaliação de licitações com configuração personalizada...")
            
            # Atualizar thresholds se fornecidos
            update_similarity_thresholds(config)
            
            # Criar vetorizador baseado na configuração
            vectorizer_type = config.get('vectorizer_type', 'hybrid')
            vectorizer = create_vectorizer(vectorizer_type)
            
            # Obter configuração de limpeza de matches
            clear_matches = config.get('clear_matches', True)
            
            # Executar reavaliação
            result = reevaluate_existing_bids(vectorizer, clear_matches=clear_matches)
            
            # Preparar mensagem de resultado
            stats = result.get('estatisticas', {}) if result else {}
            matches_count = result.get('matches_encontrados', 0) if result else 0
            
            success_message = f"Reavaliação concluída! {matches_count} matches encontrados"
            if stats.get('total_processadas', 0) > 0:
                success_rate = (stats.get('com_matches', 0) / stats['total_processadas']) * 100
                success_message += f" (taxa de sucesso: {success_rate:.1f}%)"
            
            process_status['reevaluate']['last_result'] = {
                'success': True,
                'message': success_message,
                'timestamp': datetime.datetime.now().isoformat(),
                'config_used': config,
                'statistics': stats,
                'matches_found': matches_count
            }
            logger.info("✅ Reavaliação de licitações concluída!")
            
        except Exception as e:
            error_msg = f"Erro na reavaliação: {str(e)}"
            logger.error(error_msg)
            process_status['reevaluate']['last_result'] = {
                'success': False,
                'message': error_msg,
                'timestamp': datetime.datetime.now().isoformat(),
                'error': str(e)
            }
        finally:
            process_status['reevaluate']['running'] = False
    
    # Executar em thread separada
    thread = threading.Thread(target=run_process)
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Reavaliação de licitações iniciada em background',
        'config': config
    })

@app.route('/api/status/daily-bids', methods=['GET'])
def get_daily_bids_status():
    """Status da busca de novas licitações"""
    return jsonify({
        'running': process_status['daily_bids']['running'],
        'last_result': process_status['daily_bids']['last_result']
    })

@app.route('/api/status/reevaluate', methods=['GET'])
def get_reevaluate_status():
    """Status da reavaliação de licitações"""
    return jsonify({
        'running': process_status['reevaluate']['running'],
        'last_result': process_status['reevaluate']['last_result']
    })

@app.route('/api/status', methods=['GET'])
def get_all_status():
    """Status geral de todos os processos"""
    return jsonify({
        'daily_bids': {
            'running': process_status['daily_bids']['running'],
            'last_result': process_status['daily_bids']['last_result']
        },
        'reevaluate': {
            'running': process_status['reevaluate']['running'],
            'last_result': process_status['reevaluate']['last_result']
        }
    })

@app.route('/api/config/options', methods=['GET'])
def get_config_options():
    """Obter opções de configuração disponíveis"""
    try:
        import matching
        
        # Verificar quais tipos de vetorizadores estão disponíveis
        available_vectorizers = []
        
        # Verificar OpenAI
        openai_available = bool(os.getenv('OPENAI_API_KEY'))
        
        # Verificar se Sentence Transformers está disponível
        sentence_transformers_available = True
        try:
            import sentence_transformers
        except ImportError:
            sentence_transformers_available = False
        
        # Opções de vetorização
        vectorizer_options = [
            {
                'id': 'hybrid',
                'name': 'Sistema Híbrido',
                'description': 'OpenAI + SentenceTransformers fallback (RECOMENDADO)',
                'available': openai_available or sentence_transformers_available,
                'recommended': True,
                'requires_api_key': openai_available
            },
            {
                'id': 'openai',
                'name': 'OpenAI Embeddings',
                'description': 'Alta qualidade semântica (requer API key)',
                'available': openai_available,
                'recommended': openai_available,
                'requires_api_key': True
            },
            {
                'id': 'sentence_transformers',
                'name': 'SentenceTransformers',
                'description': 'Local, gratuito, boa qualidade',
                'available': sentence_transformers_available,
                'recommended': not openai_available,
                'requires_api_key': False
            },
            {
                'id': 'mock',
                'name': 'MockTextVectorizer',
                'description': 'Básico, apenas para teste',
                'available': True,
                'recommended': False,
                'requires_api_key': False
            }
        ]
        
        # Configurações atuais
        current_config = {
            'similarity_threshold_phase1': getattr(matching, 'SIMILARITY_THRESHOLD_PHASE1', 0.65),
            'similarity_threshold_phase2': getattr(matching, 'SIMILARITY_THRESHOLD_PHASE2', 0.70),
            'max_pages': getattr(matching, 'PNCP_MAX_PAGES', 5)
        }
        
        return jsonify({
            'success': True,
            'data': {
                'vectorizer_options': vectorizer_options,
                'current_config': current_config,
                'recommended_vectorizer': 'hybrid' if (openai_available or sentence_transformers_available) else 'mock'
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter opções de configuração: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao obter opções de configuração'
        }), 500

# ==================== NOVOS ENDPOINTS PARA LICITAÇÕES DETALHADAS ====================

@app.route('/api/bids/<pncp_id>', methods=['GET'])
def get_bid_detail(pncp_id):
    """Buscar detalhes completos de uma licitação específica pelo pncp_id"""
    try:
        logger.info(f"Buscando detalhes da licitação PNCP: {pncp_id}")
        
        # Conectar ao banco PostgreSQL
        conn = get_db_connection()
        
        try:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                # Buscar licitação detalhada
                cursor.execute("""
                    SELECT * FROM licitacoes 
                    WHERE pncp_id = %s
                """, (pncp_id,))
                
                bid = cursor.fetchone()
                
                if not bid:
                    return jsonify({
                        'success': False,
                        'message': 'Licitação não encontrada'
                    }), 404
                
                # Converter para dict e formatar dados
                bid_dict = dict(bid)
                
                # Buscar itens da licitação
                cursor.execute("""
                    SELECT * FROM licitacao_itens 
                    WHERE licitacao_id = %s 
                    ORDER BY numero_item
                """, (bid_dict['id'],))
                
                itens = cursor.fetchall()
                itens_list = [dict(item) for item in itens]
                
                # Adicionar itens à licitação
                bid_dict['itens'] = itens_list
                bid_dict['possui_itens'] = len(itens_list) > 0
                
                # Converter valores Decimal para float para JSON
                for key, value in bid_dict.items():
                    if hasattr(value, '__float__'):  # Decimal types
                        bid_dict[key] = float(value)
                
                # Converter itens também
                for item in bid_dict['itens']:
                    for key, value in item.items():
                        if hasattr(value, '__float__'):
                            item[key] = float(value)
                
                return jsonify({
                    'success': True,
                    'data': bid_dict,
                    'message': f'Licitação {pncp_id} encontrada com {len(itens_list)} itens'
                })
                
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Erro ao buscar detalhes da licitação: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao buscar detalhes da licitação'
        }), 500

@app.route('/api/bids/detail', methods=['GET'])
def get_bid_detail_by_query():
    """Buscar detalhes completos de uma licitação específica pelo pncp_id via query parameter"""
    try:
        pncp_id = request.args.get('pncp_id')
        
        if not pncp_id:
            return jsonify({
                'success': False,
                'message': 'Parâmetro pncp_id é obrigatório'
            }), 400
        
        logger.info(f"Buscando detalhes da licitação PNCP: {pncp_id}")
        
        # Conectar ao banco PostgreSQL
        conn = get_db_connection()
        
        try:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                # Buscar licitação detalhada
                cursor.execute("""
                    SELECT * FROM licitacoes 
                    WHERE pncp_id = %s
                """, (pncp_id,))
                
                bid = cursor.fetchone()
                
                if not bid:
                    return jsonify({
                        'success': False,
                        'message': 'Licitação não encontrada'
                    }), 404
                
                # Converter para dict e formatar dados
                bid_dict = dict(bid)
                
                # Buscar itens da licitação
                cursor.execute("""
                    SELECT * FROM licitacao_itens 
                    WHERE licitacao_id = %s 
                    ORDER BY numero_item
                """, (bid_dict['id'],))
                
                itens = cursor.fetchall()
                itens_list = [dict(item) for item in itens]
                
                # Adicionar itens à licitação
                bid_dict['itens'] = itens_list
                bid_dict['possui_itens'] = len(itens_list) > 0
                
                # Converter valores Decimal para float para JSON
                for key, value in bid_dict.items():
                    if hasattr(value, '__float__'):  # Decimal types
                        bid_dict[key] = float(value)
                
                # Converter itens também
                for item in bid_dict['itens']:
                    for key, value in item.items():
                        if hasattr(value, '__float__'):
                            item[key] = float(value)
                
                return jsonify({
                    'success': True,
                    'data': bid_dict,
                    'message': f'Licitação {pncp_id} encontrada com {len(itens_list)} itens'
                })
                
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Erro ao buscar detalhes da licitação: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao buscar detalhes da licitação'
        }), 500

@app.route('/api/bids/<pncp_id>/items', methods=['GET'])
def get_bid_items(pncp_id):
    """Buscar itens de uma licitação específica"""
    try:
        logger.info(f"Buscando itens da licitação PNCP: {pncp_id}")
        
        # Conectar ao banco PostgreSQL
        conn = get_db_connection()
        
        try:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                # Primeiro, buscar o ID da licitação pelo pncp_id
                cursor.execute("""
                    SELECT id FROM licitacoes WHERE pncp_id = %s
                """, (pncp_id,))
                
                bid = cursor.fetchone()
                
                if not bid:
                    return jsonify({
                        'success': False,
                        'message': 'Licitação não encontrada'
                    }), 404
                
                # Buscar itens da licitação
                cursor.execute("""
                    SELECT * FROM licitacao_itens 
                    WHERE licitacao_id = %s 
                    ORDER BY numero_item
                """, (bid['id'],))
                
                itens = cursor.fetchall()
                itens_list = []
                
                # Converter e formatar dados
                for item in itens:
                    item_dict = dict(item)
                    # Converter valores Decimal para float
                    for key, value in item_dict.items():
                        if hasattr(value, '__float__'):
                            item_dict[key] = float(value)
                    itens_list.append(item_dict)
                
                return jsonify({
                    'success': True,
                    'data': itens_list,
                    'total': len(itens_list),
                    'message': f'{len(itens_list)} itens encontrados para a licitação {pncp_id}'
                })
                
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Erro ao buscar itens da licitação: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao buscar itens da licitação'
        }), 500

@app.route('/api/bids/items', methods=['GET'])
def get_bid_items_by_query():
    """Buscar itens de uma licitação específica via query parameter"""
    try:
        pncp_id = request.args.get('pncp_id')
        
        if not pncp_id:
            return jsonify({
                'success': False,
                'message': 'Parâmetro pncp_id é obrigatório'
            }), 400
        
        logger.info(f"Buscando itens da licitação PNCP: {pncp_id}")
        
        # Conectar ao banco PostgreSQL
        conn = get_db_connection()
        
        try:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                # Primeiro, buscar o ID da licitação pelo pncp_id
                cursor.execute("""
                    SELECT id FROM licitacoes WHERE pncp_id = %s
                """, (pncp_id,))
                
                bid = cursor.fetchone()
                
                if not bid:
                    return jsonify({
                        'success': False,
                        'message': 'Licitação não encontrada'
                    }), 404
                
                # Buscar itens da licitação
                cursor.execute("""
                    SELECT * FROM licitacao_itens 
                    WHERE licitacao_id = %s 
                    ORDER BY numero_item
                """, (bid['id'],))
                
                itens = cursor.fetchall()
                itens_list = []
                
                # Converter e formatar dados
                for item in itens:
                    item_dict = dict(item)
                    # Converter valores Decimal para float
                    for key, value in item_dict.items():
                        if hasattr(value, '__float__'):
                            item_dict[key] = float(value)
                    itens_list.append(item_dict)
                
                return jsonify({
                    'success': True,
                    'data': itens_list,
                    'total': len(itens_list),
                    'message': f'{len(itens_list)} itens encontrados para a licitação {pncp_id}'
                })
                
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Erro ao buscar itens da licitação: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao buscar itens da licitação'
        }), 500

@app.route('/api/bids/detailed', methods=['GET'])
def get_bids_detailed():
    """Buscar licitações com informações detalhadas (paginado)"""
    try:
        # Parâmetros de paginação
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 100)  # Máximo 100 por página
        offset = (page - 1) * limit
        
        # Filtros opcionais
        uf = request.args.get('uf')
        modalidade_id = request.args.get('modalidade_id')
        status = request.args.get('status')
        
        logger.info(f"Buscando licitações detalhadas - Página {page}, Limite {limit}")
        
        # Conectar ao banco PostgreSQL
        conn = get_db_connection()
        
        try:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                # Construir query com filtros
                where_conditions = []
                params = []
                
                if uf:
                    where_conditions.append("uf = %s")
                    params.append(uf)
                
                if modalidade_id:
                    where_conditions.append("modalidade_id = %s")
                    params.append(int(modalidade_id))
                
                if status:
                    where_conditions.append("status = %s")
                    params.append(status)
                
                where_clause = ""
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)
                
                # Buscar total de registros
                count_query = f"SELECT COUNT(*) FROM licitacoes {where_clause}"
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()[0]
                
                # Buscar licitações com paginação
                query = f"""
                    SELECT * FROM licitacoes 
                    {where_clause}
                    ORDER BY data_publicacao DESC, created_at DESC
                    LIMIT %s OFFSET %s
                """
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                bids = cursor.fetchall()
                
                # Formatar dados
                formatted_bids = []
                for bid in bids:
                    bid_dict = dict(bid)
                    # Converter valores Decimal para float
                    for key, value in bid_dict.items():
                        if hasattr(value, '__float__'):
                            bid_dict[key] = float(value)
                    formatted_bids.append(bid_dict)
                
                # Calcular metadados de paginação
                total_pages = (total_count + limit - 1) // limit
                has_next = page < total_pages
                has_prev = page > 1
                
                return jsonify({
                    'success': True,
                    'data': formatted_bids,
                    'pagination': {
                        'current_page': page,
                        'per_page': limit,
                        'total_count': total_count,
                        'total_pages': total_pages,
                        'has_next': has_next,
                        'has_prev': has_prev
                    },
                    'message': f'{len(formatted_bids)} licitações encontradas (página {page} de {total_pages})'
                })
                
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Erro ao buscar licitações detalhadas: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao buscar licitações detalhadas'
        }), 500

# ==================== ENDPOINTS DE ANÁLISE DE EDITAIS ====================

@app.route('/api/licitacoes/<licitacao_id>/analisar', methods=['POST'])
def analisar_edital(licitacao_id):
    """Iniciar análise completa do edital (processamento assíncrono)"""
    try:
        logger.info(f"Iniciando análise do edital para licitação {licitacao_id}")
        
        # Conectar ao banco
        conn = get_db_connection()
        analyzer = DocumentAnalyzer(conn)
        
        def run_analysis():
            """Executa análise em thread separada"""
            try:
                # Usar asyncio para executar função async
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(analyzer.analisar_licitacao(licitacao_id))
                logger.info(f"Análise concluída para licitação {licitacao_id}: {result.get('success')}")
            except Exception as e:
                logger.error(f"Erro na thread de análise: {e}")
            finally:
                conn.close()
        
        # Executar análise em background
        thread = threading.Thread(target=run_analysis)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Análise iniciada em background',
            'licitacao_id': licitacao_id,
            'status': 'processando'
        }), 202
        
    except Exception as e:
        logger.error(f"Erro ao iniciar análise: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/licitacoes/<licitacao_id>/checklist', methods=['GET'])
def obter_checklist(licitacao_id):
    """
    Obtém checklist da licitação.
    Implementa fluxo sequencial:
    1. Document Processor (se necessário)
    2. Edital Analyzer 
    3. Retorna checklist ou status de processamento
    """
    try:
        # Verificar se checklist já existe e está processado
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute("""
                    SELECT id, status_geracao, resumo_executivo, score_adequacao, 
                           pontos_principais, pontos_atencao, 
                           created_at, updated_at, erro_detalhes
                    FROM edital_checklists 
                    WHERE licitacao_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """, (licitacao_id,))
                
                checklist_existente = cursor.fetchone()
                
                # Se existe checklist processado com sucesso, retorna
                if checklist_existente and checklist_existente['status_geracao'] == 'concluido':
                    return jsonify({
                        'success': True,
                        'data': dict(checklist_existente),
                        'status': 'ready'
                    })
                
                # Se está processando, retorna status
                if checklist_existente and checklist_existente['status_geracao'] == 'processando':
                    return jsonify({
                        'success': True,
                        'status': 'processing',
                        'message': 'Checklist sendo gerado. Aguarde 1-2 minutos...'
                    })
                
                # Se há erro, retorna o erro
                if checklist_existente and checklist_existente['status_geracao'] == 'erro':
                    return jsonify({
                        'success': False,
                        'status': 'error',
                        'message': 'Erro na geração do checklist',
                        'error': checklist_existente.get('erro_detalhes', 'Erro desconhecido')
                    })
        
        # Se não existe checklist, acionar processamento sequencial
        return jsonify({
            'success': True,
            'status': 'starting',
            'message': 'Iniciando análise da licitação. Isso pode levar 1-2 minutos...'
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter checklist: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/licitacoes/<licitacao_id>/documentos', methods=['GET'])
def listar_documentos_edital(licitacao_id):
    """Listar documentos processados de uma licitação"""
    try:
        conn = get_db_connection()
        processor = DocumentProcessor(conn)
        
        # Buscar documentos e anexos
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("""
                SELECT e.*, 
                       COALESCE(
                           json_agg(
                               json_build_object(
                                   'id', a.id,
                                   'titulo', a.titulo,
                                   'arquivo_local', a.arquivo_local,
                                   'file_type', a.file_type,
                                   'processing_status', a.processing_status
                               )
                           ) FILTER (WHERE a.id IS NOT NULL), 
                           '[]'::json
                       ) as anexos
                FROM editais e
                LEFT JOIN edital_anexos a ON e.id = a.edital_id
                WHERE e.licitacao_id = %s
                GROUP BY e.id
                ORDER BY e.created_at DESC
            """, (licitacao_id,))
            
            documentos = cursor.fetchall()
            
        conn.close()
        
        return jsonify({
            'success': True,
            'documentos': [dict(doc) for doc in documentos]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar documentos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Novo endpoint para iniciar análise
@app.route('/api/licitacoes/<licitacao_id>/iniciar-analise', methods=['POST'])
def iniciar_analise_sequencial(licitacao_id):
    """
    Inicia análise sequencial:
    1. Document Processor (extração de ZIPs e identificação de documentos)
    2. Edital Analyzer (geração de checklist com IA)
    """
    try:
        logger.info(f"🚀 Iniciando análise sequencial para licitação: {licitacao_id}")
        
        # Marcar como iniciando no banco
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Deletar checklist anterior se existir
                cursor.execute("DELETE FROM edital_checklists WHERE licitacao_id = %s", (licitacao_id,))
                
                # Criar registro de processamento
                cursor.execute("""
                    INSERT INTO edital_checklists (
                        id, licitacao_id, status_geracao, created_at
                    ) VALUES (%s, %s, %s, %s)
                """, (str(uuid.uuid4()), licitacao_id, 'processando', datetime.datetime.now()))
                
                conn.commit()
        
        # Executar processamento em thread separada
        def processar_async():
            try:
                logger.info(f"🔍 Thread iniciada para processamento da licitação: {licitacao_id}")
                
                # PASSO 1: Document Processor
                logger.info(f"📋 PASSO 1: Processando documentos...")
                
                # Verificar conexão com banco
                try:
                    conn = get_db_connection()
                    logger.info(f"✅ Conexão com banco estabelecida")
                except Exception as e:
                    logger.error(f"❌ ERRO: Falha na conexão com banco: {e}")
                    raise
                
                # Usar o CloudDocumentProcessor (que salva no Supabase Storage)
                logger.info(f"☁️ Usando CloudDocumentProcessor para armazenamento na nuvem")
                
                try:
                    # Importar aqui para evitar imports circulares
                    from core import CloudDocumentProcessor
                    document_processor = CloudDocumentProcessor(conn)
                    logger.info(f"✅ CloudDocumentProcessor carregado com sucesso")
                except ImportError as e:
                    logger.warning(f"⚠️ CloudDocumentProcessor não disponível, usando versão local: {e}")
                    from document_processor import DocumentProcessor
                    document_processor = DocumentProcessor(conn)
                
                resultado_docs = document_processor.processar_documentos_licitacao(licitacao_id)
                
                logger.info(f"📊 Resultado do processamento de documentos: {resultado_docs}")
                
                if not resultado_docs['success']:
                    error_msg = resultado_docs.get('error', 'Erro desconhecido')
                    logger.error(f"❌ PASSO 1 FALHOU: {error_msg}")
                    raise Exception(f"Erro no processamento de documentos: {error_msg}")
                
                # Se documentos já existem, isso é OK - vamos para a análise
                if resultado_docs.get('documentos_existentes'):
                    logger.info(f"✅ PASSO 1 OK: Documentos já existem no banco - prosseguindo para análise")
                else:
                    logger.info(f"✅ PASSO 1 OK: {resultado_docs.get('message', 'Documentos processados')}")
                
                # PASSO 2: Edital Analyzer (SEMPRE executar)
                logger.info(f"🤖 PASSO 2: Gerando checklist com IA...")
                
                analyzer = DocumentAnalyzer(conn)
                
                # Aguardar análise
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                resultado_checklist = loop.run_until_complete(analyzer.analisar_licitacao(licitacao_id))
                
                logger.info(f"📊 Resultado da análise: {resultado_checklist}")
                
                if not resultado_checklist['success']:
                    error_msg = resultado_checklist.get('error', 'Erro desconhecido')
                    logger.error(f"❌ PASSO 2 FALHOU: {error_msg}")
                    raise Exception(f"Erro na análise: {error_msg}")
                
                logger.info(f"✅ PASSO 2 concluído: Checklist gerado com sucesso!")
                
                # Fechar conexão
                conn.close()
                logger.info(f"🔐 Conexão com banco fechada")
                
                return {
                    'success': True,
                    'message': 'Análise completa realizada com sucesso',
                    'documentos_processados': resultado_docs.get('total_documentos', 0),
                    'checklist_gerado': True
                }
                
            except Exception as e:
                logger.error(f"❌ Erro na análise sequencial: {e}")
                logger.error(f"🔍 Stack trace:", exc_info=True)
                
                # Marcar erro no banco
                try:
                    with get_db_connection() as conn:
                        with conn.cursor() as cursor:
                            cursor.execute("""
                                UPDATE edital_checklists 
                                SET status_geracao = 'erro', erro_detalhes = %s, updated_at = %s
                                WHERE licitacao_id = %s
                            """, (str(e), datetime.datetime.now(), licitacao_id))
                            conn.commit()
                    logger.info(f"📝 Erro marcado no banco")
                except Exception as db_error:
                    logger.error(f"❌ Erro ao marcar erro no banco: {db_error}")
                
                return {
                    'success': False,
                    'error': str(e)
                }
        
        # Executar processamento em background
        thread = threading.Thread(target=processar_async)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Análise iniciada. Verifique o status em /checklist',
            'estimated_time': '1-2 minutos'
        })
        
    except Exception as e:
        logger.error(f"Erro ao iniciar análise sequencial: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== FIM DOS NOVOS ENDPOINTS ====================

if __name__ == '__main__':
    print("🚀 Iniciando API Flask...")
    print("📊 Endpoints disponíveis:")
    print("   - GET  /api/health")
    print("   - GET  /api/bids") 
    print("   - GET  /api/bids/detailed")
    print("   - GET  /api/bids/<pncp_id>")
    print("   - GET  /api/bids/<pncp_id>/items")
    print("   - GET  /api/companies")
    print("   - POST /api/companies")
    print("   - PUT  /api/companies/<id>")
    print("   - DEL  /api/companies/<id>")
    print("   - GET  /api/matches")
    print("   - GET  /api/matches/by-company")
    print("   - GET  /api/status")
    print("   - POST /api/search-new-bids")
    print("   - POST /api/reevaluate-bids")
    print("   🤖 Análise de Editais (RAG):")
    print("   - POST /api/licitacoes/<id>/analisar")
    print("   - GET  /api/licitacoes/<id>/checklist") 
    print("   - GET  /api/licitacoes/<id>/checklist/status")
    print("\n💡 Acesse http://localhost:5001/api/health para testar")
    
    app.run(host='0.0.0.0', port=5001, debug=True) 