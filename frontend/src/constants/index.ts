import { VectorizerConfig } from '../types';

export const API_BASE_URL = 'http://localhost:5001/api';

export const VECTORIZER_OPTIONS: VectorizerConfig[] = [
  // {
  //   type: 'hybrid',
  //   name: 'Sistema Híbrido',
  //   description: 'OpenAI + SentenceTransformers como fallback (Recomendado)',
  //   icon: 'brain',
  //   requiresApiKey: false,
  //   performance: 'high',
  //   cost: 'paid'
  // },
  // {
  //   type: 'openai',
  //   name: 'OpenAI Embeddings',
  //   description: 'Alta qualidade semântica, requer chave API',
  //   icon: 'zap',
  //   requiresApiKey: true,
  //   performance: 'high',
  //   cost: 'paid'
  // },
  {
    type: 'sentence_transformers',
    name: 'SentenceTransformers',
    description: 'Modelo local, gratuito, boa qualidade',
    icon: 'target',
    requiresApiKey: false,
    performance: 'medium',
    cost: 'free'
  }
  // {
  //   type: 'mock',
  //   name: 'MockTextVectorizer',
  //   description: 'Sistema básico para testes (não recomendado)',
  //   icon: 'settings',
  //   requiresApiKey: false,
  //   performance: 'low',
  //   cost: 'free'
  // }
]; 