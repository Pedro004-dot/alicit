#!/usr/bin/env python3
"""
Módulo de vetorização de texto para matching de licitações
Contém diferentes implementações de vetorização: OpenAI, SentenceTransformers, Híbrido e Mock
"""

import os
import requests
import re
import numpy as np
from typing import List, Dict, Any
from abc import ABC, abstractmethod
from unidecode import unidecode

# --- Stopwords em português ---
PORTUGUESE_STOPWORDS = {
    'a', 'ao', 'aos', 'aquela', 'aquelas', 'aquele', 'aqueles', 'aquilo', 'as', 'até', 'com', 'como', 
    'da', 'das', 'de', 'dela', 'delas', 'dele', 'deles', 'do', 'dos', 'e', 'é', 'ela', 'elas', 'ele', 
    'eles', 'em', 'entre', 'era', 'eram', 'essa', 'essas', 'esse', 'esses', 'esta', 'está', 'estamos', 
    'estão', 'estar', 'estas', 'estava', 'estavam', 'este', 'esteja', 'estejam', 'estejamos', 'estes', 
    'esteve', 'estive', 'estivemos', 'estiver', 'estivera', 'estiveram', 'estiverem', 'estivermos', 
    'estivesse', 'estivessem', 'estivéramos', 'estivéssemos', 'estou', 'eu', 'foi', 'fomos', 'for', 
    'fora', 'foram', 'forem', 'formos', 'fosse', 'fossem', 'fui', 'fôramos', 'fôssemos', 'haja', 
    'hajam', 'hajamos', 'hão', 'havemos', 'havia', 'hei', 'houve', 'houvemos', 'houver', 'houvera', 
    'houveram', 'houverei', 'houverem', 'houveremos', 'houveria', 'houveriam', 'houvermos', 'houverá', 
    'houverão', 'houveremos', 'houvesse', 'houvessem', 'houvéramos', 'houvéssemos', 'há', 'isso', 
    'isto', 'já', 'lhe', 'lhes', 'mais', 'mas', 'me', 'mesmo', 'meu', 'meus', 'minha', 'minhas', 
    'muito', 'na', 'nas', 'nem', 'no', 'nos', 'nossa', 'nossas', 'nosso', 'nossos', 'não', 'nós', 
    'o', 'os', 'ou', 'para', 'pela', 'pelas', 'pelo', 'pelos', 'por', 'qual', 'quando', 'que', 
    'quem', 'são', 'se', 'seja', 'sejam', 'sejamos', 'sem', 'ser', 'será', 'serão', 'seu', 'seus', 
    'só', 'sua', 'suas', 'também', 'te', 'tem', 'temos', 'tenha', 'tenham', 'tenhamos', 'tenho', 
    'ter', 'teu', 'teus', 'teve', 'tinha', 'tinham', 'tive', 'tivemos', 'tiver', 'tivera', 'tiveram', 
    'tiverem', 'tivermos', 'tivesse', 'tivessem', 'tivéramos', 'tivéssemos', 'tu', 'tua', 'tuas', 
    'tém', 'tínhamos', 'um', 'uma', 'você', 'vocês', 'vos'
}

# --- Expansão de siglas técnicas ---
TECHNICAL_EXPANSIONS = {
    'ti': 'tecnologia da informação',
    'tic': 'tecnologia da informação e comunicação',
    'rh': 'recursos humanos',
    'gps': 'sistema de posicionamento global',
    'cpu': 'unidade central de processamento',
    'hd': 'disco rígido',
    'ssd': 'solid state drive',
    'ram': 'memória de acesso aleatório',
    'led': 'diodo emissor de luz',
    'lcd': 'display de cristal líquido',
    'usb': 'universal serial bus',
    'wifi': 'wireless fidelity',
    'lan': 'rede local',
    'wan': 'rede de área ampla',
    'erp': 'enterprise resource planning',
    'crm': 'customer relationship management',
    'api': 'interface de programação de aplicações',
    'sql': 'structured query language',
    'pdf': 'portable document format',
    'xml': 'extensible markup language',
    'html': 'hypertext markup language',
    'http': 'hypertext transfer protocol',
    'https': 'hypertext transfer protocol secure',
    'ftp': 'file transfer protocol',
    'smtp': 'simple mail transfer protocol',
    'dns': 'domain name system',
    'dhcp': 'dynamic host configuration protocol',
    'voip': 'voice over internet protocol',
    'pbx': 'private branch exchange',
    'cftv': 'circuito fechado de televisão',
    'dvr': 'digital video recorder',
    'nvr': 'network video recorder',
    'ip': 'internet protocol',
    'tcp': 'transmission control protocol',
    'udp': 'user datagram protocol'
}


class BaseTextVectorizer(ABC):
    """Classe abstrata base para vetorização de texto"""
    
    @abstractmethod
    def vectorize(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def batch_vectorize(self, texts: List[str]) -> List[List[float]]:
        pass

    def preprocess_text(self, text: str) -> str:
        """Pré-processamento avançado de texto em português"""
        if not text:
            return ""
        
        # Converter para minúsculas
        text = text.lower()
        
        # Remover acentos
        text = unidecode(text)
        
        # Expandir siglas técnicas
        words = text.split()
        expanded_words = []
        for word in words:
            # Remover pontuação da palavra para verificar sigla
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word in TECHNICAL_EXPANSIONS:
                expanded_words.append(TECHNICAL_EXPANSIONS[clean_word])
            else:
                expanded_words.append(word)
        text = ' '.join(expanded_words)
        
        # Remover caracteres especiais mas manter espaços
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remover números isolados (manter quando fazem parte de palavras)
        text = re.sub(r'\b\d+\b', '', text)
        
        # Remover stopwords
        words = text.split()
        filtered_words = [word for word in words if word not in PORTUGUESE_STOPWORDS and len(word) > 2]
        
        # Reconstruir texto
        text = ' '.join(filtered_words)
        
        # Normalizar espaços
        text = ' '.join(text.split())
        
        return text.strip()


class OpenAITextVectorizer(BaseTextVectorizer):
    """Vetorizador usando OpenAI Embeddings API - Melhor qualidade semântica"""
    
    def __init__(self, model: str = "text-embedding-3-large"):
        self.model = model
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY não encontrada nas variáveis de ambiente")
        
        # Headers para requisições
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # URL da API
        self.url = "https://api.openai.com/v1/embeddings"
        print(f"🔥 OpenAI Embeddings inicializado - Modelo: {self.model}")
    
    def vectorize(self, text: str) -> List[float]:
        """Vetoriza um único texto usando OpenAI"""
        if not text or not text.strip():
            return []
        
        # Preprocessar texto
        clean_text = self.preprocess_text(text)
        if not clean_text:
            return []
        
        # Limitar tamanho (OpenAI tem limite de tokens)
        if len(clean_text) > 8000:
            clean_text = clean_text[:8000] + "..."
        
        payload = {
            "model": self.model,
            "input": clean_text,
            "encoding_format": "float"
        }
        
        try:
            response = requests.post(self.url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            embedding = data['data'][0]['embedding']
            
            print(f"   🔢 OpenAI embedding: {len(embedding)} dimensões")
            return embedding
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na API OpenAI: {e}")
            return []
    
    def batch_vectorize(self, texts: List[str]) -> List[List[float]]:
        """Vetoriza múltiplos textos em batch (mais eficiente)"""
        if not texts:
            return []
        
        # Preprocessar textos
        clean_texts = []
        for text in texts:
            if text and text.strip():
                clean_text = self.preprocess_text(text)
                if clean_text:
                    # Limitar tamanho
                    if len(clean_text) > 8000:
                        clean_text = clean_text[:8000] + "..."
                    clean_texts.append(clean_text)
        
        if not clean_texts:
            return []
        
        payload = {
            "model": self.model,
            "input": clean_texts,
            "encoding_format": "float"
        }
        
        try:
            print(f"   🔄 Processando batch OpenAI: {len(clean_texts)} textos...")
            response = requests.post(self.url, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            embeddings = [item['embedding'] for item in data['data']]
            
            print(f"   ✅ Batch OpenAI processado: {len(embeddings)} embeddings de {len(embeddings[0])} dimensões")
            return embeddings
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na API OpenAI (batch): {e}")
            return []


class SentenceTransformersVectorizer(BaseTextVectorizer):
    """Vetorizador usando Sentence Transformers (local, gratuito) - Para português"""
    
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Modelos testados para português:
        - sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (recomendado)
        - sentence-transformers/all-MiniLM-L6-v2 (mais rápido)
        - neuralmind/bert-base-portuguese-cased (específico para português)
        """
        try:
            from sentence_transformers import SentenceTransformer
            print(f"🔄 Carregando modelo Sentence Transformers: {model_name}...")
            self.model = SentenceTransformer(model_name)
            print(f"✅ Modelo carregado: {self.model.get_sentence_embedding_dimension()} dimensões")
        except ImportError:
            raise ImportError("sentence-transformers não instalado. Execute: pip install sentence-transformers")
        except Exception as e:
            print(f"❌ Erro ao carregar modelo: {e}")
            raise
    
    def vectorize(self, text: str) -> List[float]:
        """Vetoriza um único texto"""
        if not text or not text.strip():
            return []
        
        clean_text = self.preprocess_text(text)
        if not clean_text:
            return []
        
        # Limitar tamanho (modelos BERT têm limite de tokens)
        if len(clean_text) > 5000:
            clean_text = clean_text[:5000] + "..."
        
        try:
            embedding = self.model.encode(clean_text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            print(f"❌ Erro no SentenceTransformers: {e}")
            return []
    
    def batch_vectorize(self, texts: List[str]) -> List[List[float]]:
        """Vetoriza múltiplos textos de uma vez (mais eficiente)"""
        if not texts:
            return []
        
        clean_texts = []
        for text in texts:
            if text and text.strip():
                clean_text = self.preprocess_text(text)
                if clean_text:
                    # Limitar tamanho
                    if len(clean_text) > 5000:
                        clean_text = clean_text[:5000] + "..."
                    clean_texts.append(clean_text)
        
        if not clean_texts:
            return []
        
        try:
            print(f"   🔄 Processando batch SentenceTransformers: {len(clean_texts)} textos...")
            embeddings = self.model.encode(clean_texts, convert_to_numpy=True, show_progress_bar=True)
            result = [embedding.tolist() for embedding in embeddings]
            print(f"   ✅ Batch processado: {len(result)} embeddings de {len(result[0])} dimensões")
            return result
        except Exception as e:
            print(f"❌ Erro no SentenceTransformers (batch): {e}")
            return []


class HybridTextVectorizer(BaseTextVectorizer):
    """Sistema híbrido: OpenAI como primário, SentenceTransformers como fallback"""
    
    def __init__(self):
        self.use_openai = bool(os.getenv('OPENAI_API_KEY'))
        
        if self.use_openai:
            try:
                self.primary = OpenAITextVectorizer()
                print("🔥 Sistema Híbrido: OpenAI como vetorizador principal")
            except Exception as e:
                print(f"⚠️  Falha ao inicializar OpenAI: {e}")
                self.use_openai = False
        
        if not self.use_openai:
            print("⚠️  OPENAI_API_KEY não encontrada ou falha, usando SentenceTransformers")
        
        # Fallback sempre disponível
        try:
            self.fallback = SentenceTransformersVectorizer()
            print("✅ SentenceTransformers carregado como fallback")
        except Exception as e:
            print(f"❌ Erro crítico: Não foi possível carregar nem OpenAI nem SentenceTransformers: {e}")
            raise
    
    def vectorize(self, text: str) -> List[float]:
        if self.use_openai:
            try:
                result = self.primary.vectorize(text)
                if result:  # Se sucesso, retorna
                    return result
            except Exception as e:
                print(f"⚠️  OpenAI falhou, usando fallback: {e}")
        
        return self.fallback.vectorize(text)
    
    def batch_vectorize(self, texts: List[str]) -> List[List[float]]:
        if self.use_openai:
            try:
                result = self.primary.batch_vectorize(texts)
                if result:  # Se sucesso, retorna
                    return result
            except Exception as e:
                print(f"⚠️  OpenAI falhou, usando fallback: {e}")
        
        return self.fallback.batch_vectorize(texts)


class MockTextVectorizer(BaseTextVectorizer):
    """Vetorizador mock baseado em palavras-chave para demonstração - DEPRECATED"""
    
    def __init__(self):
        print("⚠️  AVISO: Usando MockTextVectorizer (DEPRECATED)")
        print("   Para melhor performance, configure OPENAI_API_KEY ou use SentenceTransformers")
        
        # Categorias e suas palavras-chave EXPANDIDAS
        self.categories = {
            'informatica': [
                'computador', 'notebook', 'servidor', 'software', 'hardware', 'monitor', 
                'impressora', 'scanner', 'mouse', 'teclado', 'cpu', 'memoria', 'processador', 
                'desktop', 'microcontrolador', 'raspberry', 'pi', 'tecnologia', 'ti', 'informatica',
                'equipamento', 'digital', 'eletronico', 'sistema', 'dados', 'programacao',
                'tecnologia da informacao', 'tic', 'unidade central de processamento',
                'disco rigido', 'solid state drive', 'memoria de acesso aleatorio'
            ],
            'impressao': [
                'impressora', 'toner', 'cartucho', 'papel', 'impressao', 'multifuncional', 
                'scanner', 'copiadora', 'xerox', 'copia', 'digitalizacao', 'corporativa',
                'outsourcing', 'servico', 'manutencao'
            ],
            'rede': [
                'rede', 'switch', 'roteador', 'cabo', 'cabeamento', 'wifi', 'ethernet', 
                'firewall', 'modem', 'internet', 'conectividade', 'infraestrutura', 
                'telecomunicacao', 'wireless', 'fibra', 'wireless fidelity', 'rede local',
                'rede de area ampla', 'internet protocol', 'voice over internet protocol'
            ],
            'moveis': [
                'mesa', 'cadeira', 'armario', 'estante', 'arquivo', 'mobiliario', 'movel',
                'escritorio', 'bancada', 'gaveta', 'prateleira'
            ],
            'construcao': [
                'obra', 'construcao', 'reforma', 'pintura', 'eletrica', 'hidraulica', 'civil',
                'engenharia', 'instalacao', 'manutencao', 'reparo'
            ],
            'seguranca': [
                'cftv', 'camera', 'seguranca', 'monitoramento', 'alarme', 'controle acesso',
                'circuito fechado de televisao', 'digital video recorder', 'network video recorder'
            ],
            'veiculo': [
                'veiculo', 'carro', 'caminhao', 'onibus', 'motocicleta', 'combustivel',
                'manutencao veicular', 'sistema de posicionamento global'
            ]
        }
    
    def vectorize(self, text: str) -> List[float]:
        if not text:
            return [0.0] * len(self.categories)
        
        # Aplicar pré-processamento
        text_processed = self.preprocess_text(text)
        
        vector = []
        
        for category, keywords in self.categories.items():
            score = 0
            for keyword in keywords:
                if keyword in text_processed:
                    score += 1
            
            # Normalizar por número de palavras-chave na categoria
            normalized_score = min(score / len(keywords), 1.0)
            vector.append(normalized_score)
        
        return vector
    
    def batch_vectorize(self, texts: List[str]) -> List[List[float]]:
        return [self.vectorize(text) for text in texts]


def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calcula similaridade de cosseno entre dois vetores"""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    
    # Converter para numpy arrays
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    
    # Calcular produto escalar
    dot_product = np.dot(v1, v2)
    
    # Calcular normas
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    
    # Evitar divisão por zero
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    # Converter resultado numpy para float Python nativo
    similarity = float(dot_product / (norm1 * norm2))
    return similarity


def calculate_enhanced_similarity(vec1: List[float], vec2: List[float], text1: str = "", text2: str = "") -> tuple[float, str]:
    """
    Calcula similaridade aprimorada combinando cosseno com outros fatores
    Retorna (score, justificativa)
    """
    # Similaridade base (cosseno)
    cosine_score = calculate_cosine_similarity(vec1, vec2)
    
    # Fatores adicionais se textos forem fornecidos
    bonus_factors = []
    
    if text1 and text2:
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        # Bonus por palavras exatas em comum
        words1 = set(text1_lower.split())
        words2 = set(text2_lower.split())
        common_words = words1.intersection(words2)
        
        if common_words:
            word_bonus = min(len(common_words) * 0.05, 0.2)  # Máximo 20% bonus
            cosine_score += word_bonus
            bonus_factors.append(f"palavras comuns: {', '.join(list(common_words)[:3])}")
        
        # Bonus por siglas/acrônimos
        tech_terms = ['ti', 'tic', 'cpu', 'gps', 'led', 'usb', 'wifi', 'cftv', 'api', 'erp']
        common_tech = [term for term in tech_terms if term in text1_lower and term in text2_lower]
        if common_tech:
            tech_bonus = min(len(common_tech) * 0.03, 0.1)  # Máximo 10% bonus
            cosine_score += tech_bonus
            bonus_factors.append(f"termos técnicos: {', '.join(common_tech)}")
    
    # Garantir que não passe de 1.0
    final_score = min(cosine_score, 1.0)
    
    # Criar justificativa
    justificativa = f"Similaridade cosseno: {cosine_score:.3f}"
    if bonus_factors:
        justificativa += f" + bônus ({'; '.join(bonus_factors)})"
    
    return final_score, justificativa 