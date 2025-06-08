import React from 'react';
import { TabType } from '../types';

interface NavigationProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  bidsCount: number;
  companiesCount: number;
  matchesCount: number;
  companyMatchesCount: number;
}

const Navigation: React.FC<NavigationProps> = ({
  activeTab,
  setActiveTab,
  bidsCount,
  companiesCount,
  matchesCount,
  companyMatchesCount
}) => {
  const tabs = [
    { id: 'config' as TabType, label: '⚙️ Configurações' },
    { id: 'bids' as TabType, label: `Licitações (${bidsCount})` },
    { id: 'companies' as TabType, label: `Empresas (${companiesCount})` },
    { id: 'matches' as TabType, label: `Matches (${matchesCount})` },
    { id: 'company-matches' as TabType, label: `Matches por Empresa (${companyMatchesCount})` }
  ];

  return (
    <div className="border-b border-gray-200 mb-6">
      <nav className="-mb-px flex space-x-8">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === tab.id
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </div>
  );
};

export default Navigation; 