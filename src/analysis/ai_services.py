"""
Módulo de serviços de IA para análise de editais
Contém classes para geração de embeddings e checklists usando OpenAI
"""

import os
import json
import logging
import openai
from typing import List, Dict, Optional, Any
from datetime import datetime

# Configurar logging
logger = logging.getLogger(__name__)

# Configurar OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')


class EmbeddingGenerator:
    """Classe para gerar embeddings com OpenAI"""
    
    def __init__(self):
        self.model = "text-embedding-ada-002"
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    async def gerar_embedding(self, texto: str) -> List[float]:
        """Gera embedding para um texto"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texto
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            raise


class ChecklistGenerator:
    """Classe para gerar checklists automáticos usando GPT"""
    
    def __init__(self):
        self.model = "gpt-4"
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    async def gerar_checklist(self, contexto_documentos: str, objeto_licitacao: str) -> Dict:
        """Gera checklist estruturado baseado no conteúdo dos documentos"""
        try:
            prompt = self._construir_prompt_checklist(contexto_documentos, objeto_licitacao)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "Você é um especialista em licitações públicas brasileiras. Analise o edital e gere um checklist estruturado e detalhado."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=3000
            )
            
            # Parse da resposta JSON
            checklist_text = response.choices[0].message.content
            checklist_data = self._parse_checklist_response(checklist_text)
            
            return checklist_data
            
        except Exception as e:
            logger.error(f"Erro ao gerar checklist: {e}")
            raise
    
    def _construir_prompt_checklist(self, contexto: str, objeto: str) -> str:
        """Constrói prompt para geração do checklist"""
        return f"""
Você é um especialista em licitações públicas brasileiras. Analise cuidadosamente o edital fornecido e extraia TODAS as informações solicitadas de forma precisa e estruturada.

OBJETO DA LICITAÇÃO: {objeto}

CONTEÚDO DO EDITAL:
{contexto[:8000]}  # Limitar contexto

INSTRUÇÕES IMPORTANTES:
1. Leia todo o conteúdo com atenção para encontrar as informações específicas
2. Se uma informação não estiver claramente disponível, marque como "Não informado" 
3. Para datas, use o formato DD/MM/AAAA
4. Para valores monetários, extraia o valor numérico e indique a moeda
5. Para horários, use o formato HH:MM
6. Seja preciso com números de licitação, modalidades e nomes de órgãos
7. **MUITO IMPORTANTE**: Para score_adequacao, SEMPRE use um número de 0.0 a 10.0 (nunca texto)

Gere um checklist estruturado no seguinte formato JSON:
{{
    "informacoes_basicas": {{
        "nome_orgao": "Nome completo do órgão/entidade",
        "data_abertura": "DD/MM/AAAA",
        "horario_abertura": "HH:MM",
        "modalidade": "Tipo da modalidade (pregão eletrônico, concorrência, etc.)",
        "numero_licitacao": "Número completo da licitação",
        "valor_estimado": {{
            "valor": 0.0,
            "moeda": "BRL",
            "descricao": "Descrição do valor se houver"
        }},
        "recursos_financeiros": "Fonte dos recursos/dotação orçamentária",
        "objeto_detalhado": "Descrição completa do objeto da licitação"
    }},
    "resumo_executivo": "Resumo conciso da licitação em 2-3 frases",
    "pontos_principais": [
        {{
            "item": "Título do ponto principal",
            "descricao": "Descrição detalhada",
            "status": "obrigatorio|recomendado|opcional"
        }}
    ],
    "criterios_habilitacao": {{
        "juridica": ["Documentos jurídicos necessários"],
        "tecnica": ["Requisitos técnicos obrigatórios"],
        "economica": ["Documentos econômico-financeiros"],
        "regularidade_fiscal": ["Certidões e comprovações fiscais"]
    }},
    "prazos_importantes": [
        {{
            "evento": "Nome do evento/prazo",
            "data": "DD/MM/AAAA",
            "horario": "HH:MM",
            "tipo": "abertura|entrega|impugnacao|esclarecimento|outros",
            "observacoes": "Detalhes adicionais se houver"
        }}
    ],
    "proposta_comercial": {{
        "criterio_julgamento": "menor_preco|melhor_tecnica|tecnica_preco|maior_lance",
        "forma_pagamento": "Condições de pagamento",
        "prazo_execucao": "Prazo para execução do objeto",
        "local_execucao": "Local onde será executado o objeto"
    }},
    "documentos_necessarios": [
        "Lista detalhada de todos os documentos obrigatórios para participação"
    ],
    "observacoes_importantes": [
        "Pontos de atenção especiais",
        "Requisitos específicos",
        "Restrições ou condições especiais"
    ],
    "contatos": {{
        "responsavel": "Nome do responsável",
        "telefone": "Telefone para contato",
        "email": "Email para esclarecimentos",
        "endereco": "Endereço do órgão"
    }},
    "score_adequacao": 7.5,
    "observacoes_extracao": "Comentários sobre a qualidade da extração"
}}

**ATENÇÃO ESPECIAL PARA O SCORE:**
- score_adequacao DEVE ser um número decimal entre 0.0 e 10.0
- Use 8.0-10.0 para editais muito completos e bem estruturados
- Use 6.0-7.9 para editais com informações suficientes
- Use 4.0-5.9 para editais com algumas lacunas
- Use 0.0-3.9 para editais com muitas informações faltando
- **NUNCA use texto como "Não informado" para o score**

ATENÇÃO: 
- Extraia as informações EXATAMENTE como aparecem no documento
- Se houver múltiplas datas/horários, identifique qual é a data de abertura das propostas
- Para modalidades, use os termos exatos (Pregão Eletrônico, Concorrência Pública, etc.)
- No número da licitação, inclua o ano e formatação completa
- Para recursos financeiros, procure por dotação orçamentária, fonte de recursos, etc.

Responda APENAS com o JSON válido, sem explicações adicionais.
"""
    
    def _parse_checklist_response(self, response_text: str) -> Dict:
        """Faz parse da resposta do GPT para extrair JSON"""
        try:
            # Tentar extrair JSON da resposta
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_text = response_text[start_idx:end_idx]
                return json.loads(json_text)
            else:
                # Fallback se não encontrar JSON
                return self._criar_checklist_fallback()
                
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao fazer parse do JSON: {e}")
            return self._criar_checklist_fallback()
    
    def _criar_checklist_fallback(self) -> Dict:
        """Cria checklist básico como fallback"""
        return {
            "informacoes_basicas": {
                "nome_orgao": "Não informado",
                "data_abertura": "Não informado",
                "horario_abertura": "Não informado",
                "modalidade": "Não informado",
                "numero_licitacao": "Não informado",
                "valor_estimado": {
                    "valor": 0.0,
                    "moeda": "BRL",
                    "descricao": "Não informado"
                },
                "recursos_financeiros": "Não informado",
                "objeto_detalhado": "Não informado"
            },
            "resumo_executivo": "Licitação processada com sucesso. Aguardando análise detalhada.",
            "pontos_principais": [
                {
                    "item": "Documentação Básica",
                    "descricao": "Verificar documentos obrigatórios para participação",
                    "status": "obrigatorio"
                }
            ],
            "criterios_habilitacao": {
                "juridica": ["Documentos da empresa"],
                "tecnica": ["Qualificação técnica"],
                "economica": ["Comprovação financeira"],
                "regularidade_fiscal": ["Certidões fiscais"]
            },
            "prazos_importantes": [],
            "proposta_comercial": {
                "criterio_julgamento": "menor_preco",
                "forma_pagamento": "Não informado",
                "prazo_execucao": "Não informado",
                "local_execucao": "Não informado"
            },
            "documentos_necessarios": ["A definir"],
            "observacoes_importantes": ["Checklist gerado automaticamente"],
            "contatos": {
                "responsavel": "Não informado",
                "telefone": "Não informado",
                "email": "Não informado",
                "endereco": "Não informado"
            },
            "score_adequacao": 5.0,
            "observacoes_extracao": "Fallback - informações limitadas"
        } 