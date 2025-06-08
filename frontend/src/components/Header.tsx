import React from 'react';

const Header: React.FC = () => {
  return (
    <div className="mb-8">
      <h1 className="text-4xl font-bold text-gray-900 mb-2">
        🏛️ Sistema de Matching de Licitações
      </h1>
      <p className="text-lg text-gray-600">
        Busque e analise licitações do PNCP com matching automático de empresas
      </p>
    </div>
  );
};

export default Header; 