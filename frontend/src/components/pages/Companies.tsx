import React from 'react';
import CompaniesTab from '../tabs/CompaniesTab';
import { Company } from '../../types';

interface CompaniesPageProps {
  companies: Company[];
  loading: boolean;
  onReload: () => void;
}

const CompaniesPage: React.FC<CompaniesPageProps> = ({ companies, loading, onReload }) => {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <span className="mr-3">🏢</span>
              Empresas
            </h1>
            <p className="text-gray-600 mt-1">
              Cadastre, edite e gerencie todas as empresas no sistema
            </p>
          </div>
          <div className="bg-green-100 text-green-800 px-4 py-2 rounded-lg">
            <span className="font-semibold">{companies.length}</span> empresas
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <CompaniesTab companies={companies} loading={loading} onReload={onReload} />
      </div>
    </div>
  );
};

export default CompaniesPage; 