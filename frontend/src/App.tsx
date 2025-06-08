import React, { useState } from 'react';
import { MatchingConfig } from './types';
import { useApiData } from './hooks/useApiData';
import { useConfigActions } from './hooks/useConfigActions';

// Componentes
import Navbar from './components/Navbar';
import HomePage from './components/pages/Home';
import BidsPage from './components/pages/Bids';
import CompaniesPage from './components/pages/Companies';
import MatchingPage from './components/pages/Matching';

const App: React.FC = () => {
  // Estados para navegação e configuração
  const [activePage, setActivePage] = useState<'home' | 'bids' | 'companies' | 'matching'>('home');
  const [config, setConfig] = useState<MatchingConfig>({
    vectorizer_type: 'sentence_transformers',
    similarity_threshold_phase1: 0.65,
    similarity_threshold_phase2: 0.70,
    max_pages: 5,
    clear_matches: true
  });
  const [showAdvancedConfig, setShowAdvancedConfig] = useState(false);

  // Hook para dados da API
  const {
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
  } = useApiData();

  // Polling de status (verifica a cada 3 segundos quando algum processo está rodando)
  const pollStatus = () => {
    const interval = setInterval(async () => {
      await loadStatus();
    }, 3000);

    // Para o polling após 60 segundos
    setTimeout(() => {
      clearInterval(interval);
    }, 60000);
  };

  // Hook para ações de configuração
  const { error, handleSearchNewBids, handleReevaluateBids } = useConfigActions({
    config,
    setLoading,
    loadBids,
    loadMatches,
    pollStatus
  });

  // Renderizar conteúdo baseado na página ativa
  const renderPageContent = () => {
    switch (activePage) {
      case 'home':
        return (
          <HomePage
            config={config}
            setConfig={setConfig}
            showAdvancedConfig={showAdvancedConfig}
            setShowAdvancedConfig={setShowAdvancedConfig}
            status={status}
            loading={loading}
            error={error}
            onSearchNewBids={handleSearchNewBids}
            onReevaluateBids={handleReevaluateBids}
            bidsCount={bids.length}
            companiesCount={companies.length}
            matchesCount={matches.length}
          />
        );
      case 'bids':
        return <BidsPage bids={bids} loading={loading.bids || false} />;
      case 'companies':
        return <CompaniesPage companies={companies} loading={loading.companies || false} onReload={loadCompanies} />;
      case 'matching':
        return <MatchingPage matches={matches} companyMatches={companyMatches} loading={{
          matches: loading.matches || false,
          companyMatches: loading.companyMatches || false
        }} />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar fixa */}
      <Navbar 
        activePage={activePage} 
        setActivePage={setActivePage}
        bidsCount={bids.length}
        companiesCount={companies.length}
        matchesCount={matches.length}
      />

      {/* Container principal com padding para compensar a navbar fixa */}
      <div className="pt-16">
        <div className="max-w-7xl mx-auto p-6">
          {renderPageContent()}
        </div>
      </div>
    </div>
  );
};

export default App;
