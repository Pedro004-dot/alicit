import React from 'react';
import { Brain, Zap, Target, Settings } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { MatchingConfig } from '../../types';
import { VECTORIZER_OPTIONS } from '../../constants';
import { getPerformanceColor, getCostColor } from '../../utils';

interface VectorizerSelectionProps {
  config: MatchingConfig;
  setConfig: React.Dispatch<React.SetStateAction<MatchingConfig>>;
}

const VectorizerSelection: React.FC<VectorizerSelectionProps> = ({ config, setConfig }) => {
  const getIconComponent = (iconType: string) => {
    switch (iconType) {
      case 'brain': return <Brain className="h-5 w-5" />;
      case 'zap': return <Zap className="h-5 w-5" />;
      case 'target': return <Target className="h-5 w-5" />;
      case 'settings': return <Settings className="h-5 w-5" />;
      default: return <Settings className="h-5 w-5" />;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5" />
          Sistema de Vetorização (IA)
        </CardTitle>
        <p className="text-sm text-gray-600">
          Escolha o sistema de IA para análise semântica das licitações
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {VECTORIZER_OPTIONS.map((option) => (
          <div
            key={option.type}
            className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
              config.vectorizer_type === option.type
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => setConfig(prev => ({ ...prev, vectorizer_type: option.type }))}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded ${config.vectorizer_type === option.type ? 'bg-blue-200' : 'bg-gray-100'}`}>
                  {getIconComponent(option.icon)}
                </div>
                <div>
                  <h3 className="font-semibold text-lg">{option.name}</h3>
                  <p className="text-gray-600 mb-2">{option.description}</p>
                  <div className="flex gap-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPerformanceColor(option.performance)}`}>
                      Performance: {option.performance === 'high' ? 'Alta' : option.performance === 'medium' ? 'Média' : 'Baixa'}
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCostColor(option.cost)}`}>
                      {option.cost === 'free' ? 'Gratuito' : 'Pago'}
                    </span>
                    {option.requiresApiKey && (
                      <span className="px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                        Requer API Key
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className={`w-5 h-5 rounded-full border-2 ${
                config.vectorizer_type === option.type
                  ? 'border-blue-500 bg-blue-500'
                  : 'border-gray-300'
              }`}>
                {config.vectorizer_type === option.type && (
                  <div className="w-full h-full rounded-full bg-white scale-50"></div>
                )}
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

export default VectorizerSelection; 