import React from 'react';
import { Loader2, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Status } from '../types';

interface StatusCardsProps {
  status: {
    daily_bids: Status;
    reevaluate: Status;
  } | null;
}

const StatusCards: React.FC<StatusCardsProps> = ({ status }) => {
  const getStatusIcon = (processStatus: Status) => {
    if (processStatus.running) {
      return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
    }
    if (processStatus.last_result?.success) {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    }
    if (processStatus.last_result?.success === false) {
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    }
    return <Clock className="h-4 w-4 text-gray-400" />;
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return 'Data não disponível';
    try {
      return new Date(timestamp).toLocaleString('pt-BR');
    } catch {
      return 'Data inválida';
    }
  };

  if (!status) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {getStatusIcon(status.daily_bids)}
            Busca de Novas Licitações
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm">
            Status: {status.daily_bids.running ? 'Executando...' : 'Parado'}
          </p>
          {status.daily_bids.last_result && (
            <div className="mt-2 text-xs text-gray-600">
              <p>Último resultado: {status.daily_bids.last_result.message || 'Sem mensagem'}</p>
              <p>Em: {formatTimestamp(status.daily_bids.last_result.timestamp)}</p>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {getStatusIcon(status.reevaluate)}
            Reavaliação de Licitações
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm">
            Status: {status.reevaluate.running ? 'Executando...' : 'Parado'}
          </p>
          {status.reevaluate.last_result && (
            <div className="mt-2 text-xs text-gray-600">
              <p>Último resultado: {status.reevaluate.last_result.message || 'Sem mensagem'}</p>
              <p>Em: {formatTimestamp(status.reevaluate.last_result.timestamp)}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default StatusCards; 