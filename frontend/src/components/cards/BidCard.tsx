import React from 'react';
import { Bid } from '../../types';
import { formatCurrency, formatDate } from '../../utils';

interface BidCardProps {
  bid: Bid;
  onClick?: (pncp_id: string) => void;
}

const BidCard: React.FC<BidCardProps> = ({ bid, onClick }) => {
  const handleClick = () => {
    if (onClick) {
      onClick(bid.pncp_id);
    }
  };

  return (
    <div 
      className={`bg-white rounded-lg shadow-md p-6 border-l-4 border-[#FF7610] hover:shadow-lg transition-shadow duration-200 ${
        onClick ? 'cursor-pointer hover:bg-gray-50' : ''
      }`}
      onClick={handleClick}
    >
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
            {bid.objeto_compra}
          </h3>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span className="bg-[#FFD2B3] text-[#CC5F0D] px-2 py-1 rounded-full text-xs font-medium">
              {bid.modalidade_nome || 'Modalidade não informada'}
            </span>
            <span>{bid.uf}</span>
          </div>
        </div>
        
        {onClick && (
          <div className="flex-shrink-0 ml-4">
            <button 
              className="text-gray-400 hover:text-[#FF7610] transition-colors p-1"
              onClick={(e) => {
                e.stopPropagation();
                handleClick();
              }}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </button>
          </div>
        )}
      </div>

      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Valor Estimado:</span>
          <span className="text-lg font-semibold text-green-600">
            {bid.valor_total_estimado ? formatCurrency(bid.valor_total_estimado) : 'Sigiloso'}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Data de Publicação:</span>
          <span className="text-sm text-gray-900">
            {bid.data_publicacao ? formatDate(bid.data_publicacao) : 'Data não informada'}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Status:</span>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
            bid.status === 'ativo' 
              ? 'bg-green-100 text-green-800'
              : 'bg-gray-100 text-gray-800'
          }`}>
            {bid.status}
          </span>
        </div>

        <div className="pt-2 border-t border-gray-100">
          <div className="flex justify-between items-center text-xs text-gray-500">
            <span>PNCP: {bid.pncp_id}</span>
            {onClick && (
              <span className="text-[#FF7610] hover:text-[#FF7610]">
                Clique para ver detalhes →
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BidCard; 