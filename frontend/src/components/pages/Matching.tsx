import React, { useState } from 'react';
import MatchesTab from '../tabs/MatchesTab';
import CompanyMatchesTab from '../tabs/CompanyMatchesTab';
import { Match, CompanyMatch } from '../../types';

interface MatchingPageProps {
  matches: Match[];
  companyMatches: CompanyMatch[];
  loading: {
    matches: boolean;
    companyMatches: boolean;
  };
}

const MatchingPage: React.FC<MatchingPageProps> = ({ matches, companyMatches, loading }) => {
  const [activeView, setActiveView] = useState<'general' | 'company'>('general');

  const totalMatches = matches.length + companyMatches.length;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <span className="mr-3">🔗</span>
              Central de Matching
            </h1>
            <p className="text-gray-600 mt-1">
              Visualize e analise todos os matches entre empresas e licitações
            </p>
          </div>
          <div className="bg-purple-100 text-purple-800 px-4 py-2 rounded-lg">
            <span className="font-semibold">{totalMatches}</span> matches encontrados
          </div>
        </div>
      </div>

      {/* View Toggle */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-1">
        <div className="flex space-x-1">
          <button
            onClick={() => setActiveView('general')}
            className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeView === 'general'
                ? 'bg-blue-100 text-blue-800 border border-blue-200'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            <span className="mr-2">📊</span>
            Matches Gerais ({matches.length})
          </button>
          <button
            onClick={() => setActiveView('company')}
            className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeView === 'company'
                ? 'bg-green-100 text-green-800 border border-green-200'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            <span className="mr-2">🏢</span>
            Matches por Empresa ({companyMatches.length})
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {activeView === 'general' ? (
          <MatchesTab matches={matches} loading={loading.matches} />
        ) : (
          <CompanyMatchesTab companyMatches={companyMatches} loading={loading.companyMatches} />
        )}
      </div>
    </div>
  );
};

export default MatchingPage; 