import React, { useState } from 'react';
import { Loader2, Plus } from 'lucide-react';
import { Company } from '../../types';
import CompanyCard from '../cards/CompanyCard';
import CompanyModal from '../modals/CompanyModal';
import DeleteConfirmModal from '../modals/DeleteConfirmModal';
import { useCompanyCrud } from '../../hooks/useCompanyCrud';

interface CompaniesTabProps {
  companies: Company[];
  loading: boolean;
  onReload?: () => void; // Função para recarregar a lista após operações CRUD
}

const CompaniesTab: React.FC<CompaniesTabProps> = ({ companies, loading, onReload }) => {
  const [showCompanyModal, setShowCompanyModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [editingCompany, setEditingCompany] = useState<Company | null>(null);
  const [deletingCompany, setDeletingCompany] = useState<Company | null>(null);

  const {
    loading: crudLoading,
    error: crudError,
    createCompany,
    updateCompany,
    deleteCompany,
    clearError
  } = useCompanyCrud(() => {
    // Callback executado após sucesso nas operações CRUD
    setShowCompanyModal(false);
    setShowDeleteModal(false);
    setEditingCompany(null);
    setDeletingCompany(null);
    onReload?.(); // Recarrega a lista
  });

  const handleCreateCompany = () => {
    setEditingCompany(null);
    clearError();
    setShowCompanyModal(true);
  };

  const handleEditCompany = (company: Company) => {
    setEditingCompany(company);
    clearError();
    setShowCompanyModal(true);
  };

  const handleDeleteCompany = (company: Company) => {
    setDeletingCompany(company);
    clearError();
    setShowDeleteModal(true);
  };

  const handleSaveCompany = async (companyData: Omit<Company, 'id' | 'created_at' | 'updated_at'>) => {
    if (editingCompany) {
      // Atualizar empresa existente
      await updateCompany(editingCompany.id, companyData);
    } else {
      // Criar nova empresa
      await createCompany(companyData);
    }
  };

  const handleConfirmDelete = async () => {
    if (deletingCompany) {
      await deleteCompany(deletingCompany.id);
    }
  };

  const handleCloseModals = () => {
    setShowCompanyModal(false);
    setShowDeleteModal(false);
    setEditingCompany(null);
    setDeletingCompany(null);
    clearError();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Carregando empresas...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header com botão de criar */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">
          Empresas ({companies.length})
        </h2>
        <button
          onClick={handleCreateCompany}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Nova Empresa
        </button>
      </div>

      {/* Erro das operações CRUD */}
      {crudError && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Erro</h3>
              <div className="mt-2 text-sm text-red-700">
                {crudError}
              </div>
              <div className="mt-3">
                <button
                  onClick={clearError}
                  className="text-sm bg-red-100 text-red-800 px-3 py-1 rounded-md hover:bg-red-200 transition-colors"
                >
                  Fechar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Lista de empresas */}
      {companies.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-500 mb-4">Nenhuma empresa cadastrada</div>
          <button
            onClick={handleCreateCompany}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Cadastrar Primeira Empresa
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {companies.map((company) => (
            <CompanyCard
              key={company.id}
              company={company}
              onEdit={handleEditCompany}
              onDelete={handleDeleteCompany}
            />
          ))}
        </div>
      )}

      {/* Modais */}
      <CompanyModal
        isOpen={showCompanyModal}
        onClose={handleCloseModals}
        onSave={handleSaveCompany}
        company={editingCompany}
        loading={crudLoading}
      />

      <DeleteConfirmModal
        isOpen={showDeleteModal}
        onClose={handleCloseModals}
        onConfirm={handleConfirmDelete}
        title="Excluir Empresa"
        message={
          deletingCompany
            ? `Tem certeza que deseja excluir a empresa "${deletingCompany.nome_fantasia}"? Esta ação não pode ser desfeita.`
            : ''
        }
        loading={crudLoading}
      />
    </div>
  );
};

export default CompaniesTab; 