export interface Bid {
  id: string;
  pncp_id: string;
  objeto_compra: string;
  valor_total_estimado?: number;
  uf?: string;
  status?: string;
  data_publicacao?: string;
  modalidade_nome?: string;
  orgao_cnpj?: string;
  ano_compra?: number;
  sequencial_compra?: number;
  link_sistema_origem?: string;
  data_inclusao_db?: string;
  situacao_compra_nome?: string;
  data_abertura_proposta?: string;
  data_encerramento_proposta?: string;
  valor_total_homologado?: number;
  created_at?: string;
  updated_at?: string;
}

// Nova interface para dados detalhados da licitação (todos os campos do banco)
export interface BidDetail {
  id: string;
  pncp_id: string;
  orgao_cnpj: string;
  ano_compra: number;
  sequencial_compra: number;
  objeto_compra: string;
  link_sistema_origem?: string;
  data_publicacao?: string;
  valor_total_estimado?: number;
  uf?: string;
  status?: string;
  
  // Campos detalhados adicionados
  modalidade_nome?: string;
  modalidade_id?: number;
  situacao_compra_nome?: string;
  situacao_compra_id?: number;
  
  // Datas importantes
  data_abertura_proposta?: string;
  data_encerramento_proposta?: string;
  data_inclusao?: string;
  data_publicacao_pncp?: string;
  data_atualizacao?: string;
  
  // Valores financeiros
  valor_total_homologado?: number;
  
  // Informações processuais
  processo?: string;
  numero_compra?: string;
  numero_controle_pncp?: string;
  informacao_complementar?: string;
  justificativa_presencial?: string;
  link_processo_eletronico?: string;
  
  // Flags e configurações
  srp?: boolean;
  modo_disputa_id?: number;
  modo_disputa_nome?: string;
  
  // Dados estruturados (JSONB)
  orgao_entidade?: {
    cnpj: string;
    razaoSocial: string;
    poderId?: string;
    esferaId?: string;
  };
  
  unidade_orgao?: {
    ufNome: string;
    codigoUnidade: string;
    nomeUnidade: string;
    ufSigla: string;
    municipioNome: string;
    codigoIbge: string;
  };
  
  amparo_legal?: {
    descricao: string;
    nome: string;
    codigo: number;
  };
  
  // Tipo de instrumento
  tipo_instrumento_convocatorio_codigo?: number;
  tipo_instrumento_convocatorio_nome?: string;
  
  // Dados de controle
  possui_itens?: boolean;
  data_ultima_sincronizacao?: string;
  data_inclusao_db?: string;
  created_at?: string;
  updated_at?: string;
  
  // Backup completo das APIs
  dados_api_completos?: any;
  
  // Itens relacionados (quando incluídos)
  itens?: BidItem[];
}

// Interface para itens da licitação
export interface BidItem {
  id: string;
  licitacao_id: string;
  numero_item: number;
  descricao: string;
  quantidade?: number;
  unidade_medida?: string;
  valor_unitario_estimado?: number;
  
  // Campos detalhados adicionados
  material_ou_servico?: string;
  valor_total?: number;
  criterio_julgamento_nome?: string;
  criterio_julgamento_id?: number;
  situacao_item?: string;
  situacao_item_id?: number;
  
  // Códigos e classificações
  codigo_produto_servico?: string;
  codigo_classificacao?: string;
  grupo_item?: string;
  classe_item?: string;
  
  // Benefícios
  beneficio_micro_epp?: boolean;
  beneficio_local?: boolean;
  
  // Dados técnicos
  especificacao_tecnica?: string;
  observacoes?: string;
  
  // Controle
  created_at?: string;
  updated_at?: string;
  dados_api_completos?: any;
}

export interface Company {
  id: string;
  nome_fantasia: string;
  razao_social: string;
  cnpj?: string;
  descricao_servicos_produtos: string;
  palavras_chave?: string[] | null;
  setor_atuacao?: string;
  data_inclusao_db?: string;
  created_at?: string;
  updated_at?: string;
}

// Match com estrutura real do banco (join entre matches, licitacoes e empresas)
export interface Match {
  id: string;
  empresa_id: string;
  licitacao_id: string;
  score_similaridade: number;
  match_type: string;
  justificativa_match?: string;
  data_match: string;
  created_at?: string;
  updated_at?: string;
  empresa: {
    nome_fantasia: string;
    razao_social: string;
    cnpj?: string;
    setor_atuacao?: string;
  };
  licitacao: {
    pncp_id: string;
    objeto_compra: string;
    valor_total_estimado?: number;
    uf?: string;
    status?: string;
    data_publicacao?: string;
    modalidade_nome?: string;
  };
}

// Para a agregação de matches por empresa
export interface CompanyMatch {
  empresa_id: string;
  empresa_nome: string;
  razao_social: string;
  cnpj?: string;
  setor_atuacao?: string;
  total_matches: number;
  score_medio: number;
  melhor_score: number;
  pior_score: number;
  matches: Match[];
}

// Status dos processos
export interface Status {
  running: boolean;
  last_result?: {
    success?: boolean;
    message?: string;
    error?: string;
    timestamp?: string;
    bids_processed?: number;
    matches_found?: number;
    companies_processed?: number;
  } | null;
}

// Configuração de matching
export interface MatchingConfig {
  vectorizer_type: 'sentence_transformers' | 'openai' | 'hybrid' | 'mock';
  similarity_threshold_phase1: number;
  similarity_threshold_phase2: number;
  max_pages: number;
  clear_matches: boolean;
}

// Resposta padrão da API
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  total?: number;
}

// Tipos específicos para formulários
export interface CompanyFormData {
  nome_fantasia: string;
  razao_social: string;
  cnpj?: string;
  descricao_servicos_produtos: string;
  palavras_chave?: string[];
  setor_atuacao?: string;
}

// Tipo para abas/páginas (usado anteriormente)
export type TabType = 'bids' | 'companies' | 'matches' | 'company-matches' | 'config';

export interface ProcessStatus {
  running: boolean;
  last_result?: {
    success: boolean;
    message: string;
    timestamp: string;
    error?: string;
  };
}

export interface ApiStatus {
  daily_bids: ProcessStatus;
  reevaluate: ProcessStatus;
}

export interface VectorizerConfig {
  type: 'hybrid' | 'openai' | 'sentence_transformers' | 'mock';
  name: string;
  description: string;
  icon: string;
  requiresApiKey?: boolean;
  performance: 'high' | 'medium' | 'low';
  cost: 'free' | 'paid';
}

export interface DashboardStats {
  totalBids: number;
  totalCompanies: number;
  totalMatches: number;
  successRate: number;
} 