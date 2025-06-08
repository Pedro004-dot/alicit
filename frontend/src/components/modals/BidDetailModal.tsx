import React, { useState, useEffect } from 'react';
import { BidDetail, BidItem } from '../../types';
import { formatCurrency, formatDate } from '../../utils';

interface BidDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  pncp_id: string;
}

interface ChecklistData {
  id?: string;
  licitacao_id?: string;
  edital_id?: string;
  resumo_executivo: string;
  pontos_principais: Array<{
    item: string;
    descricao: string;
    status: string;
  }>;
  criterios_habilitacao: {
    juridica?: string[];
    tecnica?: string[];
    economica?: string[];
  };
  prazos_importantes: Array<{
    evento: string;
    prazo: string;
    tipo: string;
  }>;
  valores_referencias: {
    total?: number;
    moeda?: string;
    criterio?: string;
  };
  documentos_necessarios: string[];
  pontos_atencao: string[];
  score_adequacao: number;
}

interface ChecklistResponse {
  success: boolean;
  message?: string;
  checklist?: ChecklistData;
  data?: ChecklistData;
  status?: string;
  error?: string;
}

const BidDetailModal: React.FC<BidDetailModalProps> = ({ isOpen, onClose, pncp_id }) => {
  const [bidDetail, setBidDetail] = useState<BidDetail | null>(null);
  const [bidItems, setBidItems] = useState<BidItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'details' | 'items' | 'analysis'>('details');
  
  // Estados para análise do edital
  const [checklist, setChecklist] = useState<ChecklistData | null>(null);
  const [checklistLoading, setChecklistLoading] = useState(false);
  const [checklistError, setChecklistError] = useState<string | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState<'idle' | 'processing' | 'completed' | 'error'>('idle');

  useEffect(() => {
    if (isOpen && pncp_id) {
      fetchBidDetail();
    } else if (!isOpen) {
      // Resetar estados quando o modal fechar
      setBidDetail(null);
      setBidItems([]);
      setChecklist(null);
      setAnalysisStatus('idle');
      setChecklistLoading(false);
      setChecklistError(null);
      setActiveTab('details');
    }
  }, [isOpen, pncp_id]);

  // Iniciar análise automaticamente quando os dados da licitação forem carregados
  useEffect(() => {
    if (bidDetail?.id && !checklist && analysisStatus === 'idle') {
      console.log('🎯 Modal aberto - iniciando análise automática da licitação:', bidDetail.id);
      iniciarAnaliseSequencial();
    }
  }, [bidDetail, checklist, analysisStatus]);

  // Buscar checklist quando a aba de análise for ativada (mantido para compatibilidade)
  useEffect(() => {
    if (activeTab === 'analysis' && pncp_id && !checklist && analysisStatus === 'idle') {
      iniciarAnaliseSequencial();
    }
  }, [activeTab, pncp_id, checklist, analysisStatus]);

  const fetchBidDetail = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Usar query parameter ao invés de path parameter para evitar problemas com "/" no pncp_id
      const response = await fetch(`http://localhost:5001/api/bids/detail?pncp_id=${encodeURIComponent(pncp_id)}`);
      if (!response.ok) {
        throw new Error('Falha ao carregar detalhes da licitação');
      }
      const data = await response.json();
      setBidDetail(data.data); // Note que a resposta vem em data.data
      
      // Buscar itens também - usando query parameter para evitar problemas com "/" no pncp_id
      const itemsResponse = await fetch(`http://localhost:5001/api/bids/items?pncp_id=${encodeURIComponent(pncp_id)}`);
      if (itemsResponse.ok) {
        const itemsData = await itemsResponse.json();
        setBidItems(itemsData.data || []); // Note que a resposta vem em data.data
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
    } finally {
      setLoading(false);
    }
  };

  const iniciarAnaliseSequencial = async () => {
    if (!bidDetail?.id) return;
    
    setChecklistLoading(true);
    setChecklistError(null);
    setAnalysisStatus('processing');
    
    try {
      // PASSO 1: Iniciar análise sequencial
      console.log('🚀 Iniciando análise sequencial...');
      
      const iniciarResponse = await fetch(
        `http://localhost:5001/api/licitacoes/${bidDetail.id}/iniciar-analise`, 
        { method: 'POST' }
      );
      
      const iniciarData = await iniciarResponse.json();
      
      if (!iniciarData.success) {
        throw new Error(iniciarData.error || 'Erro ao iniciar análise');
      }
      
      console.log('✅ Análise iniciada, aguardando processamento...');
      
      // PASSO 2: Polling do status do checklist
      await pollChecklistStatus();
      
    } catch (err) {
      console.error('❌ Erro na análise:', err);
      setChecklistError(err instanceof Error ? err.message : 'Erro desconhecido');
      setAnalysisStatus('error');
      setChecklistLoading(false);
    }
  };

  const pollChecklistStatus = async () => {
    if (!bidDetail?.id) return;
    
    const maxAttempts = 24; // 2 minutos máximo (24 * 5s)
    let attempts = 0;
    
    const poll = async (): Promise<void> => {
      try {
        attempts++;
        console.log(`📊 Polling tentativa ${attempts}/${maxAttempts}...`);
        
        const response = await fetch(`http://localhost:5001/api/licitacoes/${bidDetail.id}/checklist`);
        const data: ChecklistResponse = await response.json();
        
        if (data.success) {
          if (data.status === 'ready' && data.data) {
            // ✅ Checklist pronto!
            console.log('🎉 Checklist gerado com sucesso!');
            setChecklist(data.data as ChecklistData);
            setAnalysisStatus('completed');
            setChecklistLoading(false);
            return;
          } 
          else if (data.status === 'processing') {
            // ⏳ Ainda processando
            console.log('⏳ Ainda processando, aguardando...');
            
            if (attempts < maxAttempts) {
              setTimeout(poll, 5000); // Aguardar 5 segundos
            } else {
              throw new Error('Timeout: Análise demorou mais que o esperado');
            }
            return;
          }
          else if (data.status === 'error') {
            // ❌ Erro no processamento
            throw new Error(data.error || 'Erro no processamento');
          }
          else if (data.status === 'starting') {
            // 🚀 Análise iniciando
            console.log('🚀 Análise iniciando...');
            
            if (attempts < maxAttempts) {
              setTimeout(poll, 3000); // Aguardar 3 segundos
            } else {
              throw new Error('Timeout: Análise não iniciou');
            }
            return;
          }
        } else {
          throw new Error(data.error || 'Erro na resposta da API');
        }
        
      } catch (err) {
        console.error('❌ Erro no polling:', err);
        setChecklistError(err instanceof Error ? err.message : 'Erro desconhecido');
        setAnalysisStatus('error');
        setChecklistLoading(false);
      }
    };
    
    // Iniciar polling
    setTimeout(poll, 2000); // Aguardar 2 segundos inicial
  };

  const fetchChecklist = async () => {
    // Método mantido para compatibilidade, mas agora redireciona para o fluxo sequencial
    await iniciarAnaliseSequencial();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'obrigatorio':
        return 'text-red-600 bg-red-50';
      case 'recomendado':
        return 'text-yellow-600 bg-yellow-50';
      case 'opcional':
        return 'text-green-600 bg-green-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const renderAnalysisContent = () => {
    if (checklistLoading) {
      return (
        <div className="flex items-center justify-center p-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-6"></div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">
              Analisando Documentos com IA
            </h3>
            <p className="text-gray-600 mb-4">
              {analysisStatus === 'processing' ? (
                <>
                  🤖 Extraindo e analisando documentos da licitação...<br/>
                  📊 Gerando checklist personalizado com inteligência artificial
                </>
              ) : 'Iniciando análise...'}
            </p>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-md mx-auto">
              <p className="text-sm text-blue-700 mb-2">
                ⏱️ <strong>Tempo estimado:</strong> 1-2 minutos
              </p>
              <p className="text-sm text-blue-600">
                💡 Nossa IA está processando todos os documentos (editais, anexos, termos de referência) 
                para criar uma análise detalhada e identificar os pontos mais importantes.
              </p>
            </div>
          </div>
        </div>
      );
    }

    if (checklistError) {
      return (
        <div className="p-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span className="text-red-800">Erro ao carregar análise</span>
            </div>
            <p className="text-red-700 mt-2">{checklistError}</p>
            <button 
              onClick={fetchChecklist}
              className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Tentar Novamente
            </button>
          </div>
        </div>
      );
    }

    if (!checklist) {
      return (
        <div className="p-6 text-center">
          <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-gray-600 mb-4">Nenhuma análise disponível</p>
          <button 
            onClick={fetchChecklist}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Analisar Edital
          </button>
        </div>
      );
    }

    return (
      <div className="p-6 space-y-6">
        {/* Score de Adequação */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-blue-900">Score de Adequação</h3>
            <div className="flex items-center">
              <span className="text-2xl font-bold text-blue-600">{checklist.score_adequacao}</span>
              <span className="text-blue-600 ml-1">/10</span>
            </div>
          </div>
        </div>

        {/* Resumo Executivo */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Resumo Executivo</h3>
          <p className="text-gray-700 leading-relaxed">{checklist.resumo_executivo}</p>
        </div>

        {/* Pontos Principais */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Pontos Principais</h3>
          <div className="space-y-3">
            {(checklist.pontos_principais || []).map((ponto, index) => (
              <div key={index} className="border-l-4 border-blue-400 pl-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{ponto.item}</h4>
                    <p className="text-gray-600 mt-1">{ponto.descricao}</p>
                  </div>
                  <span className={`ml-3 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(ponto.status)}`}>
                    {ponto.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Critérios de Habilitação */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Critérios de Habilitação</h3>
          <div className="grid md:grid-cols-3 gap-4">
            {Object.entries(checklist.criterios_habilitacao || {}).map(([tipo, criterios]) => (
              <div key={tipo} className="bg-gray-50 rounded-lg p-3">
                <h4 className="font-medium text-gray-900 mb-2 capitalize">{tipo}</h4>
                <ul className="space-y-1">
                  {(criterios || []).map((criterio, index) => (
                    <li key={index} className="text-sm text-gray-600 flex items-start">
                      <span className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                      {criterio}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Prazos Importantes */}
        {(checklist.prazos_importantes || []).length > 0 && (
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Prazos Importantes</h3>
            <div className="space-y-2">
              {(checklist.prazos_importantes || []).map((prazo, index) => (
                <div key={index} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0">
                  <div>
                    <span className="font-medium text-gray-900">{prazo.evento}</span>
                    <span className="ml-2 px-2 py-1 rounded-full text-xs bg-orange-100 text-orange-800">
                      {prazo.tipo}
                    </span>
                  </div>
                  <span className="text-gray-600">{prazo.prazo}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Valores de Referência */}
        {checklist.valores_referencias && (
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Valores de Referência</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-gray-600">Valor Total</span>
                <p className="text-lg font-semibold text-gray-900">
                  {checklist.valores_referencias.total 
                    ? formatCurrency(checklist.valores_referencias.total)
                    : 'Não informado'
                  }
                </p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Critério</span>
                <p className="text-lg font-semibold text-gray-900 capitalize">
                  {checklist.valores_referencias.criterio?.replace('_', ' ') || 'Não informado'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Documentos Necessários */}
        {(checklist.documentos_necessarios || []).length > 0 && (
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Documentos Necessários</h3>
            <ul className="space-y-2">
              {(checklist.documentos_necessarios || []).map((doc, index) => (
                <li key={index} className="flex items-start">
                  <svg className="w-4 h-4 text-green-500 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="text-gray-700">{doc}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Pontos de Atenção */}
        {(checklist.pontos_atencao || []).length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-yellow-900 mb-3">⚠️ Pontos de Atenção</h3>
            <ul className="space-y-2">
              {(checklist.pontos_atencao || []).map((obs, index) => (
                <li key={index} className="text-yellow-800">
                  • {obs}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <div className="flex-1">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              {bidDetail?.objeto_compra || 'Detalhes da Licitação'}
            </h2>
            
            {/* Status da Análise */}
            {bidDetail && (
              <div className="flex items-center gap-2">
                {analysisStatus === 'processing' && (
                  <div className="flex items-center gap-2 text-blue-600 bg-blue-50 px-3 py-1 rounded-full border border-blue-200">
                    <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600"></div>
                    <span className="text-xs font-medium">🤖 Analisando documentos com IA...</span>
                  </div>
                )}
                
                {analysisStatus === 'completed' && checklist && (
                  <div className="flex items-center gap-2 text-green-600 bg-green-50 px-3 py-1 rounded-full border border-green-200">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span className="text-xs font-medium">✅ Análise concluída - Score: {checklist.score_adequacao}/10</span>
                  </div>
                )}
                
                {analysisStatus === 'error' && (
                  <div className="flex items-center gap-2 text-red-600 bg-red-50 px-3 py-1 rounded-full border border-red-200">
                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    <span className="text-xs font-medium">❌ Erro na análise</span>
                  </div>
                )}
                
                {analysisStatus === 'idle' && (
                  <div className="flex items-center gap-2 text-gray-500 bg-gray-50 px-3 py-1 rounded-full border border-gray-200">
                    <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
                    <span className="text-xs font-medium">⏳ Preparando análise...</span>
                  </div>
                )}
              </div>
            )}
          </div>
          
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors p-2 hover:bg-gray-100 rounded-lg"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('details')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'details'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Detalhes
            </button>
            <button
              onClick={() => setActiveTab('items')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'items'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Itens ({bidItems.length})
            </button>
            <button
              onClick={() => setActiveTab('analysis')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'analysis'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🤖 Análise do Edital
              {analysisStatus === 'processing' && (
                <span className="ml-1 inline-block w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></span>
              )}
              {analysisStatus === 'completed' && (
                <span className="ml-1 inline-block w-2 h-2 bg-green-400 rounded-full"></span>
              )}
            </button>
          </nav>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-140px)]">
          {loading ? (
            <div className="flex items-center justify-center p-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : error ? (
            <div className="p-6">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800">Erro: {error}</p>
              </div>
            </div>
          ) : (
            <>
              {/* Detalhes Tab */}
              {activeTab === 'details' && bidDetail && (
                <div className="p-6 space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 mb-4">Informações Básicas</h3>
                      <dl className="space-y-3">
                        <div>
                          <dt className="text-sm font-medium text-gray-500">PNCP ID</dt>
                          <dd className="text-sm text-gray-900">{bidDetail.pncp_id}</dd>
                        </div>
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Status</dt>
                          <dd className="text-sm text-gray-900">{bidDetail.status || 'Não informado'}</dd>
                        </div>
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Data de Publicação</dt>
                          <dd className="text-sm text-gray-900">{bidDetail.data_publicacao ? formatDate(bidDetail.data_publicacao) : 'Não informado'}</dd>
                        </div>
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Data de Abertura</dt>
                          <dd className="text-sm text-gray-900">{bidDetail.data_abertura_proposta ? formatDate(bidDetail.data_abertura_proposta) : 'Não informado'}</dd>
                        </div>
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Data de Encerramento</dt>
                          <dd className="text-sm text-gray-900">{bidDetail.data_encerramento_proposta ? formatDate(bidDetail.data_encerramento_proposta) : 'Não informado'}</dd>
                        </div>
                      </dl>
                    </div>
                    
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 mb-4">Órgão e Valores</h3>
                      <dl className="space-y-3">
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Órgão</dt>
                          <dd className="text-sm text-gray-900">{bidDetail.orgao_entidade?.razaoSocial || 'Não informado'}</dd>
                        </div>
                        <div>
                          <dt className="text-sm font-medium text-gray-500">UF</dt>
                          <dd className="text-sm text-gray-900">{bidDetail.uf || bidDetail.unidade_orgao?.ufSigla || 'Não informado'}</dd>
                        </div>
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Valor Estimado</dt>
                          <dd className="text-sm text-gray-900">
                            {bidDetail.valor_total_estimado ? formatCurrency(bidDetail.valor_total_estimado) : 'Não informado'}
                          </dd>
                        </div>
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Modalidade</dt>
                          <dd className="text-sm text-gray-900">{bidDetail.modalidade_nome || 'Não informado'}</dd>
                        </div>
                      </dl>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Objeto da Compra</h3>
                    <p className="text-gray-700 leading-relaxed">{bidDetail.objeto_compra}</p>
                  </div>
                </div>
              )}

              {/* Itens Tab */}
              {activeTab === 'items' && (
                <div className="p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">
                    Itens da Licitação ({bidItems.length})
                  </h3>
                  {bidItems.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Item
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Descrição
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Quantidade
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Unidade
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Valor Unit.
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {bidItems.map((item, index) => (
                            <tr key={index}>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                {item.numero_item}
                              </td>
                              <td className="px-6 py-4 text-sm text-gray-900">
                                {item.descricao}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {item.quantidade}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {item.unidade_medida}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {item.valor_unitario_estimado ? formatCurrency(item.valor_unitario_estimado) : 'N/A'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-gray-500 text-center py-8">Nenhum item encontrado</p>
                  )}
                </div>
              )}

              {/* Análise Tab */}
              {activeTab === 'analysis' && renderAnalysisContent()}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default BidDetailModal; 