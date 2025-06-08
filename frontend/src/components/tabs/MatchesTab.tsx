import React, { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { Match } from '../../types';
import MatchCard from '../cards/MatchCard';
import BidDetailModal from '../modals/BidDetailModal';

interface MatchesTabProps {
  matches: Match[];
  loading: boolean;
}

const MatchesTab: React.FC<MatchesTabProps> = ({ matches, loading }) => {
  const [selectedPncpId, setSelectedPncpId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleBidClick = (pncp_id: string) => {
    setSelectedPncpId(pncp_id);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedPncpId(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-gray-600 mt-4 font-medium">Carregando matches...</p>
          <p className="text-gray-500 text-sm mt-1">Aguarde enquanto buscamos os matches</p>
        </div>
      </div>
    );
  }

  if (matches.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="bg-gray-100 rounded-full p-6 w-24 h-24 flex items-center justify-center mx-auto mb-4">
          <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhum match encontrado</h3>
        <p className="text-gray-500">Execute a busca por licitações e reavaliação para encontrar matches.</p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900">
            Matches Encontrados ({matches.length})
          </h2>
          <div className="text-sm text-gray-500 bg-blue-50 px-3 py-1 rounded-full border border-blue-200">
            💡 Clique na seção da licitação para ver todos os detalhes
          </div>
        </div>

        <div className="space-y-4">
          {matches.map((match) => (
            <MatchCard 
              key={match.id} 
              match={match} 
              onBidClick={handleBidClick}
            />
          ))}
        </div>
      </div>

      {/* Modal de Detalhes da Licitação */}
      <BidDetailModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        pncp_id={selectedPncpId || ''}
      />
    </>
  );
};

export default MatchesTab; 