import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { MatchingConfig } from '../../types';
import { VECTORIZER_OPTIONS } from '../../constants';

interface ConfigSummaryProps {
  config: MatchingConfig;
}

const ConfigSummary: React.FC<ConfigSummaryProps> = ({ config }) => {
  return (
    <Card className="bg-gradient-to-r from-blue-50 to-indigo-50">
      <CardHeader>
        <CardTitle className="text-lg">📋 Resumo da Configuração Atual</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium">Vetorizador:</span> {
              VECTORIZER_OPTIONS.find(opt => opt.type === config.vectorizer_type)?.name || 'Desconhecido'
            }
          </div>
          <div>
            <span className="font-medium">Threshold Fase 1:</span> {config.similarity_threshold_phase1}
          </div>
          <div>
            <span className="font-medium">Threshold Fase 2:</span> {config.similarity_threshold_phase2}
          </div>
          <div>
            <span className="font-medium">Máx. Páginas:</span> {config.max_pages}
          </div>
          <div>
            <span className="font-medium">Limpar Matches:</span> {config.clear_matches ? 'Sim' : 'Não'}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ConfigSummary; 