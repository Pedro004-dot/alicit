import { useState, useEffect, useCallback } from 'react';
import { Bid, Company, Match, CompanyMatch, Status, ApiResponse } from '../types';

interface LoadingState {
  bids: boolean;
  companies: boolean;
  matches: boolean;
  companyMatches: boolean;
  status: boolean;
}

interface ApiDataHook {
  bids: Bid[];
  companies: Company[];
  matches: Match[];
  companyMatches: CompanyMatch[];
  status: { daily_bids: Status; reevaluate: Status; } | null;
  loading: LoadingState;
  loadBids: () => Promise<void>;
  loadCompanies: () => Promise<void>;
  loadMatches: () => Promise<void>;
  loadStatus: () => Promise<void>;
  setLoading: (key: keyof LoadingState, value: boolean) => void;
}

const API_BASE_URL = 'http://localhost:5001/api';

export const useApiData = (): ApiDataHook => {
  const [bids, setBids] = useState<Bid[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [matches, setMatches] = useState<Match[]>([]);
  const [companyMatches, setCompanyMatches] = useState<CompanyMatch[]>([]);
  const [status, setStatus] = useState<{ daily_bids: Status; reevaluate: Status; } | null>(null);
  
  const [loading, setLoadingState] = useState<LoadingState>({
    bids: false,
    companies: false,
    matches: false,
    companyMatches: false,
    status: false,
  });

  const setLoading = useCallback((key: keyof LoadingState, value: boolean) => {
    setLoadingState(prev => ({ ...prev, [key]: value }));
  }, []);

  // Carregar licitações
  const loadBids = useCallback(async () => {
    try {
      setLoading('bids', true);
      const response = await fetch(`${API_BASE_URL}/bids`);
      
      if (!response.ok) {
        throw new Error(`Erro HTTP: ${response.status}`);
      }
      
      const result: ApiResponse<Bid[]> = await response.json();
      
      if (result.success && result.data) {
        setBids(result.data);
      } else {
        console.error('Erro na resposta da API:', result.message || result.error);
        setBids([]);
      }
    } catch (error) {
      console.error('Erro ao carregar licitações:', error);
      setBids([]);
    } finally {
      setLoading('bids', false);
    }
  }, [setLoading]);

  // Carregar empresas
  const loadCompanies = useCallback(async () => {
    try {
      setLoading('companies', true);
      const response = await fetch(`${API_BASE_URL}/companies`);
      
      if (!response.ok) {
        throw new Error(`Erro HTTP: ${response.status}`);
      }
      
      const result: ApiResponse<Company[]> = await response.json();
      
      if (result.success && result.data) {
        setCompanies(result.data);
      } else {
        console.error('Erro na resposta da API:', result.message || result.error);
        setCompanies([]);
      }
    } catch (error) {
      console.error('Erro ao carregar empresas:', error);
      setCompanies([]);
    } finally {
      setLoading('companies', false);
    }
  }, [setLoading]);

  // Carregar matches
  const loadMatches = useCallback(async () => {
    try {
      setLoading('matches', true);
      setLoading('companyMatches', true);
      
      // Carregar matches gerais
      const matchesResponse = await fetch(`${API_BASE_URL}/matches`);
      if (matchesResponse.ok) {
        const matchesResult: ApiResponse<Match[]> = await matchesResponse.json();
        if (matchesResult.success && matchesResult.data) {
          setMatches(matchesResult.data);
        }
      }
      
      // Carregar matches por empresa
      const companyMatchesResponse = await fetch(`${API_BASE_URL}/matches/by-company`);
      if (companyMatchesResponse.ok) {
        const companyMatchesResult: ApiResponse<CompanyMatch[]> = await companyMatchesResponse.json();
        if (companyMatchesResult.success && companyMatchesResult.data) {
          setCompanyMatches(companyMatchesResult.data);
        }
      }
      
    } catch (error) {
      console.error('Erro ao carregar matches:', error);
      setMatches([]);
      setCompanyMatches([]);
    } finally {
      setLoading('matches', false);
      setLoading('companyMatches', false);
    }
  }, [setLoading]);

  // Carregar status
  const loadStatus = useCallback(async () => {
    try {
      setLoading('status', true);
      const response = await fetch(`${API_BASE_URL}/status`);
      
      if (!response.ok) {
        throw new Error(`Erro HTTP: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        setStatus({
          daily_bids: result.data.daily_bids,
          reevaluate: result.data.reevaluate
        });
      } else {
        console.error('Erro na resposta da API:', result.message || result.error);
      }
    } catch (error) {
      console.error('Erro ao carregar status:', error);
    } finally {
      setLoading('status', false);
    }
  }, [setLoading]);

  // Carregar dados iniciais
  useEffect(() => {
    const loadInitialData = async () => {
      await Promise.all([
        loadBids(),
        loadCompanies(),
        loadMatches(),
        loadStatus()
      ]);
    };

    loadInitialData();
  }, [loadBids, loadCompanies, loadMatches, loadStatus]);

  return {
    bids,
    companies,
    matches,
    companyMatches,
    status,
    loading,
    loadBids,
    loadCompanies,
    loadMatches,
    loadStatus,
    setLoading
  };
}; 