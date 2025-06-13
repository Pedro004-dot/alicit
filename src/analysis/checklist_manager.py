"""
Gerenciador de checklists para análise de editais
"""
import uuid
import logging
from datetime import datetime
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class ChecklistManager:
    """Gerencia operações de checklist no banco de dados"""
    
    def __init__(self, db_connection):
        self.conn = db_connection
    
    def salvar_checklist(self, licitacao_id: str, checklist_data: Dict[str, Any]) -> str:
        """
        Salva checklist no banco de dados
        
        Args:
            licitacao_id: ID da licitação
            checklist_data: Dados do checklist gerado pela IA
            
        Returns:
            ID do checklist criado
        """
        try:
            checklist_id = str(uuid.uuid4())
            
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO edital_checklists (
                        id, licitacao_id, status_geracao, resumo_executivo, 
                        score_adequacao, pontos_principais, pontos_atencao,
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    checklist_id,
                    licitacao_id,
                    'concluido',
                    checklist_data.get('resumo_executivo', ''),
                    checklist_data.get('score_adequacao', 0),
                    checklist_data.get('pontos_principais', []),
                    checklist_data.get('pontos_atencao', []),
                    datetime.now(),
                    datetime.now()
                ))
                
                self.conn.commit()
                logger.info(f"Checklist salvo com sucesso: {checklist_id}")
                
            return checklist_id
            
        except Exception as e:
            logger.error(f"Erro ao salvar checklist: {e}")
            self.conn.rollback()
            raise
    
    async def marcar_erro_checklist(self, licitacao_id: str, erro_detalhes: str):
        """
        Marca erro na geração do checklist
        
        Args:
            licitacao_id: ID da licitação
            erro_detalhes: Detalhes do erro ocorrido
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE edital_checklists 
                    SET status_geracao = 'erro', erro_detalhes = %s, updated_at = %s
                    WHERE licitacao_id = %s
                """, (erro_detalhes, datetime.now(), licitacao_id))
                
                self.conn.commit()
                logger.info(f"Erro marcado para licitação: {licitacao_id}")
                
        except Exception as e:
            logger.error(f"Erro ao marcar erro do checklist: {e}")
            self.conn.rollback()
    
    def obter_checklist(self, licitacao_id: str) -> Optional[Dict]:
        """
        Obtém checklist da licitação
        
        Args:
            licitacao_id: ID da licitação
            
        Returns:
            Dados do checklist ou None se não encontrado
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, status_geracao, resumo_executivo, score_adequacao,
                           pontos_principais, pontos_atencao, created_at, updated_at,
                           erro_detalhes
                    FROM edital_checklists 
                    WHERE licitacao_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """, (licitacao_id,))
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        'id': result[0],
                        'status_geracao': result[1],
                        'resumo_executivo': result[2],
                        'score_adequacao': result[3],
                        'pontos_principais': result[4],
                        'pontos_atencao': result[5],
                        'created_at': result[6],
                        'updated_at': result[7],
                        'erro_detalhes': result[8]
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Erro ao obter checklist: {e}")
            return None 