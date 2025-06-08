import React, { useState } from 'react';
import { Bid } from '../../types';
import BidCard from '../cards/BidCard';
import BidDetailModal from '../modals/BidDetailModal';

interface BidsTabProps {
  bids: Bid[];
  loading: boolean;
}

const BidsTab: React.FC<BidsTabProps> = ({ bids, loading }) => {
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
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Carregando licitações...</span>
      </div>
    );
  }

  if (bids.length === 0) {
    return (
      <div className="text-center py-12">
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhuma licitação encontrada</h3>
        <p className="mt-1 text-sm text-gray-500">Execute uma busca para encontrar licitações ou aguarde o processamento.</p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900">
            Licitações Encontradas ({bids.length})
          </h2>
          <div className="text-sm text-gray-500">
            Clique em uma licitação para ver todos os detalhes
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {bids.map((bid) => (
            <BidCard 
              key={bid.id} 
              bid={bid} 
              onClick={handleBidClick}
            />
          ))}
        </div>
      </div>

      {/* Modal de Detalhes */}
      <BidDetailModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        pncp_id={selectedPncpId || ''}
      />
    </>
  );
};

export default BidsTab; 