import { useState } from 'react';
import { Company } from '../types';
import { API_BASE_URL } from '../constants';

interface UseCompanyCrudReturn {
  loading: boolean;
  error: string | null;
  createCompany: (companyData: Omit<Company, 'id' | 'created_at' | 'updated_at'>) => Promise<boolean>;
  updateCompany: (id: string, companyData: Omit<Company, 'id' | 'created_at' | 'updated_at'>) => Promise<boolean>;
  deleteCompany: (id: string) => Promise<boolean>;
  clearError: () => void;
}

export const useCompanyCrud = (onSuccess?: () => void): UseCompanyCrudReturn => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = () => setError(null);

  const createCompany = async (companyData: Omit<Company, 'id' | 'created_at' | 'updated_at'>): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/companies`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...companyData,
          // Converter array de strings para JSON se necessário
          palavras_chave: companyData.palavras_chave || []
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Erro ao criar empresa');
      }

      if (data.success) {
        onSuccess?.();
        return true;
      } else {
        throw new Error(data.message || 'Erro ao criar empresa');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const updateCompany = async (id: string, companyData: Omit<Company, 'id' | 'created_at' | 'updated_at'>): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/companies/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...companyData,
          // Converter array de strings para JSON se necessário
          palavras_chave: companyData.palavras_chave || []
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Erro ao atualizar empresa');
      }

      if (data.success) {
        onSuccess?.();
        return true;
      } else {
        throw new Error(data.message || 'Erro ao atualizar empresa');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const deleteCompany = async (id: string): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/companies/${id}`, {
        method: 'DELETE',
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Erro ao excluir empresa');
      }

      if (data.success) {
        onSuccess?.();
        return true;
      } else {
        throw new Error(data.message || 'Erro ao excluir empresa');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    error,
    createCompany,
    updateCompany,
    deleteCompany,
    clearError,
  };
}; 