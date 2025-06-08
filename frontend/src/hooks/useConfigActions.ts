import { useState, useCallback } from 'react';
import { MatchingConfig } from '../types';

// Interface para estado de loading (deve corresponder ao useApiData)
interface LoadingState {
  bids: boolean;
  companies: boolean;
  matches: boolean;
  companyMatches: boolean;
  status: boolean;
}

interface ConfigActionsParams {
  config: MatchingConfig;
  setLoading: (key: keyof LoadingState, value: boolean) => void;
  loadBids: () => Promise<void>;
  loadMatches: () => Promise<void>;
  pollStatus: () => void;
}

interface ConfigActionsHook {
  error: string | null;
  handleSearchNewBids: () => Promise<void>;
  handleReevaluateBids: () => Promise<void>;
}

const API_BASE_URL = 'http://localhost:5001/api';

export const useConfigActions = ({
  config,
  setLoading,
  loadBids,
  loadMatches,
  pollStatus
}: ConfigActionsParams): ConfigActionsHook => {
  const [error, setError] = useState<string | null>(null);

  const handleSearchNewBids = useCallback(async () => {
    try {
      setError(null);
      setLoading('status', true);

      const response = await fetch(`${API_BASE_URL}/search-new-bids`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error(`Erro ao buscar novas licitações: ${response.status}`);
      }

      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.message || 'Erro desconhecido ao buscar licitações');
      }

      // Iniciar polling para acompanhar o progresso
      pollStatus();

      // Aguardar um pouco e recarregar os dados
      setTimeout(async () => {
        await loadBids();
        await loadMatches();
      }, 2000);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(errorMessage);
      console.error('Erro ao buscar novas licitações:', err);
    } finally {
      // O loading será controlado pelo polling do status
      // setLoading('status', false);
    }
  }, [config, setLoading, loadBids, loadMatches, pollStatus]);

  const handleReevaluateBids = useCallback(async () => {
    try {
      setError(null);
      setLoading('status', true);

      const response = await fetch(`${API_BASE_URL}/reevaluate-bids`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error(`Erro ao reavaliar licitações: ${response.status}`);
      }

      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.message || 'Erro desconhecido ao reavaliar licitações');
      }

      // Iniciar polling para acompanhar o progresso
      pollStatus();

      // Aguardar um pouco e recarregar os dados
      setTimeout(async () => {
        await loadMatches();
      }, 2000);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(errorMessage);
      console.error('Erro ao reavaliar licitações:', err);
    } finally {
      // O loading será controlado pelo polling do status
      // setLoading('status', false);
    }
  }, [config, setLoading, loadMatches, pollStatus]);

  return {
    error,
    handleSearchNewBids,
    handleReevaluateBids
  };
}; 