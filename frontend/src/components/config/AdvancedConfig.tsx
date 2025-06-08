import React from 'react';
import { Cog } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { MatchingConfig } from '../../types';
import { VECTORIZER_OPTIONS } from '../../constants';

interface AdvancedConfigProps {
  config: MatchingConfig;
  setConfig: React.Dispatch<React.SetStateAction<MatchingConfig>>;
  showAdvancedConfig: boolean;
}

const AdvancedConfig: React.FC<AdvancedConfigProps> = ({ 
  config, 
  setConfig, 
  showAdvancedConfig 
}) => {
  if (!showAdvancedConfig) return null;

  return (
    <Card className="border-2 border-blue-200 bg-blue-50">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2">
          <Cog className="h-5 w-5" />
          Configurações Avançadas de Matching
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Configurações de Precisão */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold mb-2 text-gray-700">
              📊 Threshold Fase 1
            </label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.05"
              value={config.similarity_threshold_phase1}
              onChange={(e) => setConfig(prev => ({ ...prev, similarity_threshold_phase1: parseFloat(e.target.value) }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Limiar mínimo para primeira análise (0.6-0.8 recomendado)
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-semibold mb-2 text-gray-700">
              🎯 Threshold Fase 2
            </label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.05"
              value={config.similarity_threshold_phase2}
              onChange={(e) => setConfig(prev => ({ ...prev, similarity_threshold_phase2: parseFloat(e.target.value) }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Limiar final para aprovação (0.7-0.85 recomendado)
            </p>
          </div>
        </div>

        {/* Configurações de Performance */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold mb-2 text-gray-700">
              📄 Máximo de Páginas PNCP
            </label>
            <input
              type="number"
              min="1"
              max="20"
              value={config.max_pages}
              onChange={(e) => setConfig(prev => ({ ...prev, max_pages: parseInt(e.target.value) }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Limite de páginas para busca (1-10 recomendado)
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            <div>
              <label className="block text-sm font-semibold mb-2 text-gray-700">
                🗑️ Limpar Matches Existentes
              </label>
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.clear_matches}
                  onChange={(e) => setConfig(prev => ({ ...prev, clear_matches: e.target.checked }))}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="text-sm text-gray-700">
                  Remover matches anteriores antes de reavaliar
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* Resumo da Configuração */}
        <div className="bg-gray-100 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-800 mb-2">📋 Resumo da Configuração</h4>
          <div className="text-sm text-gray-600 space-y-1">
            <p><strong>Vetorizador:</strong> {VECTORIZER_OPTIONS.find(v => v.type === config.vectorizer_type)?.name}</p>
            <p><strong>Precisão:</strong> Fase 1: {config.similarity_threshold_phase1} | Fase 2: {config.similarity_threshold_phase2}</p>
            <p><strong>Performance:</strong> Máx. {config.max_pages} páginas PNCP</p>
            <p><strong>Matches:</strong> {config.clear_matches ? 'Limpar existentes' : 'Manter existentes'}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default AdvancedConfig; 