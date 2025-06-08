import React from 'react';

interface NavbarProps {
  activePage: 'home' | 'bids' | 'companies' | 'matching';
  setActivePage: (page: 'home' | 'bids' | 'companies' | 'matching') => void;
  bidsCount: number;
  companiesCount: number;
  matchesCount: number;
}

const Navbar: React.FC<NavbarProps> = ({
  activePage,
  setActivePage,
  bidsCount,
  companiesCount,
  matchesCount
}) => {
  const navItems = [
    {
      id: 'home' as const,
      label: 'Home',
      icon: '🏠',
      description: 'Dashboard principal'
    },
    {
      id: 'bids' as const,
      label: 'Licitações',
      icon: '📋',
      description: 'Gerenciar licitações',
      badge: bidsCount
    },
    {
      id: 'companies' as const,
      label: 'Empresas',
      icon: '🏢',
      description: 'Cadastro de empresas',
      badge: companiesCount
    },
    {
      id: 'matching' as const,
      label: 'Matching',
      icon: '🔗',
      description: 'Resultados de compatibilidade',
      badge: matchesCount
    }
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 bg-white shadow-lg border-b border-gray-200 z-50">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo/Brand */}
          <div className="flex items-center space-x-3">
            <div className="text-2xl">🎯</div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Alicit</h1>
              <p className="text-xs text-gray-600">Sistema de Matching</p>
            </div>
          </div>

          {/* Navigation Items */}
          <div className="flex items-center space-x-1">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActivePage(item.id)}
                className={`
                  relative flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200
                  ${activePage === item.id
                    ? 'bg-blue-100 text-blue-700 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }
                `}
                title={item.description}
              >
                <span className="text-lg">{item.icon}</span>
                <span className="font-medium">{item.label}</span>
                
                {/* Badge com contador */}
                {item.badge !== undefined && item.badge > 0 && (
                  <span className={`
                    inline-flex items-center justify-center px-2 py-1 text-xs font-bold rounded-full
                    ${activePage === item.id
                      ? 'bg-blue-200 text-blue-800'
                      : 'bg-gray-200 text-gray-700'
                    }
                  `}>
                    {item.badge}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Status Indicator */}
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-600">Online</span>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar; 