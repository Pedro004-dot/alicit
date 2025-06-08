import React, { useState, useEffect } from 'react';
import { X, Building2, FileText, Tag, Briefcase, Hash, Users, MapPin } from 'lucide-react';
import { Company } from '../../types';

interface CompanyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (company: Omit<Company, 'id' | 'created_at' | 'updated_at'>) => void;
  company?: Company | null; // null = criar nova, Company = editar existente
  loading?: boolean;
}

const CompanyModal: React.FC<CompanyModalProps> = ({ 
  isOpen, 
  onClose, 
  onSave, 
  company = null,
  loading = false 
}) => {
  const [formData, setFormData] = useState({
    nome_fantasia: '',
    razao_social: '',
    cnpj: '',
    descricao_servicos_produtos: '',
    palavras_chave: [] as string[],
    setor_atuacao: ''
  });
  const [keywordInput, setKeywordInput] = useState('');

  // Preencher form quando estiver editando
  useEffect(() => {
    if (company) {
      setFormData({
        nome_fantasia: company.nome_fantasia || '',
        razao_social: company.razao_social || '',
        cnpj: company.cnpj || '',
        descricao_servicos_produtos: company.descricao_servicos_produtos || '',
        palavras_chave: company.palavras_chave || [],
        setor_atuacao: company.setor_atuacao || ''
      });
    } else {
      // Resetar form para nova empresa
      setFormData({
        nome_fantasia: '',
        razao_social: '',
        cnpj: '',
        descricao_servicos_produtos: '',
        palavras_chave: [],
        setor_atuacao: ''
      });
    }
    setKeywordInput('');
  }, [company, isOpen]);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const addKeyword = () => {
    if (keywordInput.trim() && !formData.palavras_chave.includes(keywordInput.trim())) {
      setFormData(prev => ({
        ...prev,
        palavras_chave: [...prev.palavras_chave, keywordInput.trim()]
      }));
      setKeywordInput('');
    }
  };

  const removeKeyword = (keyword: string) => {
    setFormData(prev => ({
      ...prev,
      palavras_chave: prev.palavras_chave.filter(k => k !== keyword)
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.nome_fantasia.trim() && formData.razao_social.trim() && formData.descricao_servicos_produtos.trim()) {
      onSave(formData);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Building2 className="h-6 w-6 text-blue-600" />
            </div>
            {company ? 'Editar Empresa' : 'Nova Empresa'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors p-2 hover:bg-gray-100 rounded-lg"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Seção: Informações Básicas */}
            <div className="space-y-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                  <Users className="h-5 w-5 text-blue-600" />
                  Informações Básicas
                </h3>
                
                <div className="space-y-4">
                  {/* Nome Fantasia */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Nome Fantasia *
                    </label>
                    <input
                      type="text"
                      value={formData.nome_fantasia}
                      onChange={(e) => handleInputChange('nome_fantasia', e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                      placeholder="Nome como a empresa é conhecida"
                      required
                    />
                  </div>

                  {/* Razão Social */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Razão Social *
                    </label>
                    <input
                      type="text"
                      value={formData.razao_social}
                      onChange={(e) => handleInputChange('razao_social', e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                      placeholder="Razão social oficial da empresa"
                      required
                    />
                  </div>

                  {/* CNPJ */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                      <Hash className="h-4 w-4 text-gray-500" />
                      CNPJ
                    </label>
                    <input
                      type="text"
                      value={formData.cnpj}
                      onChange={(e) => handleInputChange('cnpj', e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                      placeholder="00.000.000/0000-00"
                      maxLength={18}
                    />
                  </div>

                  {/* Setor de Atuação */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                      <Briefcase className="h-4 w-4 text-gray-500" />
                      Setor de Atuação
                    </label>
                    <input
                      type="text"
                      value={formData.setor_atuacao}
                      onChange={(e) => handleInputChange('setor_atuacao', e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                      placeholder="Ex: Tecnologia, Construção, Consultoria..."
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Seção: Descrição e Palavras-chave */}
            <div className="space-y-6">
              {/* Descrição de Serviços/Produtos */}
              <div className="bg-green-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                  <FileText className="h-5 w-5 text-green-600" />
                  Descrição dos Serviços
                </h3>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Serviços e Produtos Oferecidos *
                  </label>
                  <textarea
                    value={formData.descricao_servicos_produtos}
                    onChange={(e) => handleInputChange('descricao_servicos_produtos', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all resize-none"
                    placeholder="Descreva detalhadamente os serviços e produtos oferecidos pela empresa..."
                    rows={6}
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Seja específico sobre os serviços para melhor identificação em licitações
                  </p>
                </div>
              </div>

              {/* Palavras-chave */}
              <div className="bg-purple-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                  <Tag className="h-5 w-5 text-purple-600" />
                  Palavras-chave e Especialidades
                </h3>
                
                <div className="space-y-3">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={keywordInput}
                      onChange={(e) => setKeywordInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addKeyword())}
                      className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                      placeholder="Digite uma palavra-chave (ex: construção, software, consultoria...)"
                    />
                    <button
                      type="button"
                      onClick={addKeyword}
                      className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
                    >
                      Adicionar
                    </button>
                  </div>
                  
                  {formData.palavras_chave.length > 0 && (
                    <div>
                      <p className="text-sm text-gray-600 mb-2">
                        Palavras-chave adicionadas ({formData.palavras_chave.length}):
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {formData.palavras_chave.map((keyword, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center gap-2 px-3 py-2 bg-purple-100 text-purple-800 rounded-full text-sm font-medium border border-purple-200"
                          >
                            {keyword}
                            <button
                              type="button"
                              onClick={() => removeKeyword(keyword)}
                              className="text-purple-600 hover:text-purple-800 hover:bg-purple-200 rounded-full p-0.5 transition-colors"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {formData.palavras_chave.length === 0 && (
                    <p className="text-sm text-gray-500 italic">
                      Adicione palavras-chave para facilitar a identificação de licitações relevantes
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Botões de Ação */}
          <div className="flex justify-end gap-3 pt-8 mt-8 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-3 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors font-medium"
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading || !formData.nome_fantasia.trim() || !formData.razao_social.trim() || !formData.descricao_servicos_produtos.trim()}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium flex items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Salvando...
                </>
              ) : (
                <>
                  <Building2 className="h-4 w-4" />
                  {company ? 'Atualizar Empresa' : 'Criar Empresa'}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CompanyModal; 