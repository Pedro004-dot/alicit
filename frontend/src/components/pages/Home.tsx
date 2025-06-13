import React from 'react';
import { MatchingConfig, Status } from '../../types';
import StatusCards from '../StatusCards';
import ConfigurationTab from '../tabs/ConfigurationTab';

interface HomePageProps {
  config: MatchingConfig;
  setConfig: React.Dispatch<React.SetStateAction<MatchingConfig>>;
  showAdvancedConfig: boolean;
  setShowAdvancedConfig: React.Dispatch<React.SetStateAction<boolean>>;
  status: { daily_bids: Status; reevaluate: Status; } | null;
  loading: any;
  error: string | null;
  onSearchNewBids: () => void;
  onReevaluateBids: () => void;
  bidsCount: number;
  companiesCount: number;
  matchesCount: number;
}

const HomePage: React.FC<HomePageProps> = ({
  config,
  setConfig,
  showAdvancedConfig,
  setShowAdvancedConfig,
  status,
  loading,
  error,
  onSearchNewBids,
  onReevaluateBids,
  bidsCount,
  companiesCount,
  matchesCount
}) => {
  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Bem-vindo a Alicit! 
            </h1>
            <p className="text-gray-600 text-lg">
              Plataforma inteligente para matching de licitações e empresas
            </p>
          </div>
          <div className="text-6xl"></div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-r from-[#FF7610] to-[#CC5F0D] rounded-lg shadow-sm p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[#FFD2B3] text-sm font-medium">Total de Licitações</p>
              <p className="text-3xl font-bold">{bidsCount}</p>
            </div>
            <div className="text-3xl opacity-80">📋</div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg shadow-sm p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100 text-sm font-medium">Empresas Cadastradas</p>
              <p className="text-3xl font-bold">{companiesCount}</p>
            </div>
            <div className="text-3xl opacity-80">🏢</div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg shadow-sm p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100 text-sm font-medium">Matches Encontrados</p>
              <p className="text-3xl font-bold">{matchesCount}</p>
            </div>
            <div className="text-3xl opacity-80">🔗</div>
          </div>
        </div>
      </div>

      {/* Status Cards */}
      {status && <StatusCards status={status} />}

      {/* Configuration Section */}
      {/* <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200 px-6 py-4">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <span className="mr-2">⚙️</span>
            Configurações e Ações
          </h2>
          <p className="text-gray-600 mt-1">
            Configure os parâmetros de matching e execute ações do sistema
          </p>
        </div>
        
        <div className="p-6">
          {status && (
            <ConfigurationTab
              config={config}
              setConfig={setConfig}
              showAdvancedConfig={showAdvancedConfig}
              setShowAdvancedConfig={setShowAdvancedConfig}
              status={status}
              loading={loading}
              error={error}
              onSearchNewBids={onSearchNewBids}
              onReevaluateBids={onReevaluateBids}
            />
          )}
        </div>
      </div> */}

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <span className="mr-2">🚀</span>
          Ações Rápidas
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
            <h4 className="font-medium text-gray-900 mb-2">📋 Gerenciar Licitações</h4>
            <p className="text-gray-600 text-sm mb-3">
              Visualize e gerencie todas as licitações disponíveis na plataforma
            </p>
            <span className="text-[#FF7610] text-sm font-medium">Ver licitações →</span>
          </div>
          
          <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
            <h4 className="font-medium text-gray-900 mb-2">🏢 Cadastrar Empresas</h4>
            <p className="text-gray-600 text-sm mb-3">
              Adicione, edite ou remova empresas do sistema de matching
            </p>
            <span className="text-green-600 text-sm font-medium">Gerenciar empresas →</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage; 