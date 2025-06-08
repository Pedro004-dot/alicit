import React from 'react';
import BidsTab from '../tabs/BidsTab';
import { Bid } from '../../types';

interface BidsPageProps {
  bids: Bid[];
  loading: boolean;
}

const BidsPage: React.FC<BidsPageProps> = ({ bids, loading }) => {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <span className="mr-3">📋</span>
              Licitações
            </h1>
            <p className="text-gray-600 mt-1">
              Gerencie todas as licitações disponíveis na plataforma
            </p>
          </div>
          <div className="bg-blue-100 text-blue-800 px-4 py-2 rounded-lg">
            <span className="font-semibold">{bids.length}</span> licitações
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <BidsTab bids={bids} loading={loading} />
      </div>
    </div>
  );
};

export default BidsPage; 