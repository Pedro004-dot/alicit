import React from 'react';
import { Loader2 } from 'lucide-react';
import { CompanyMatch } from '../../types';
import CompanyMatchCard from '../cards/CompanyMatchCard';

interface CompanyMatchesTabProps {
  companyMatches: CompanyMatch[];
  loading: boolean;
}

const CompanyMatchesTab: React.FC<CompanyMatchesTabProps> = ({ companyMatches, loading }) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Carregando matches por empresa...</span>
      </div>
    );
  }

  if (companyMatches.length === 0) {
    return (
      <p className="text-center py-8 text-gray-500">Nenhum match por empresa encontrado</p>
    );
  }

  return (
    <div className="space-y-4">
      {companyMatches.map((companyMatch) => (
        <CompanyMatchCard key={companyMatch.empresa_id} companyMatch={companyMatch} />
      ))}
    </div>
  );
};

export default CompanyMatchesTab; 