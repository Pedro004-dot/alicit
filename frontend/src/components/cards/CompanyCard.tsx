import React from 'react';
import { Edit3, Trash2, Building2, Tag } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Company } from '../../types';

interface CompanyCardProps {
  company: Company;
  onEdit?: (company: Company) => void;
  onDelete?: (company: Company) => void;
}

const CompanyCard: React.FC<CompanyCardProps> = ({ company, onEdit, onDelete }) => {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-blue-600" />
            <CardTitle className="text-lg">{company.nome_fantasia}</CardTitle>
          </div>
          <div className="flex gap-2">
            {onEdit && (
              <button
                onClick={() => onEdit(company)}
                className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                title="Editar empresa"
              >
                <Edit3 className="h-4 w-4" />
              </button>
            )}
            {onDelete && (
              <button
                onClick={() => onDelete(company)}
                className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                title="Excluir empresa"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Razão Social:</span>
              <div className="text-gray-600">{company.razao_social}</div>
            </div>
            {company.cnpj && (
              <div>
                <span className="font-medium text-gray-700">CNPJ:</span>
                <div className="text-gray-600">{company.cnpj}</div>
              </div>
            )}
            {company.setor_atuacao && (
              <div>
                <span className="font-medium text-gray-700">Setor:</span>
                <div className="text-gray-600">{company.setor_atuacao}</div>
              </div>
            )}
          </div>
          
          <div>
            <span className="font-medium text-gray-700">Descrição de Serviços/Produtos:</span>
            <div className="text-gray-600 text-sm mt-1 line-clamp-3">
              {company.descricao_servicos_produtos}
            </div>
          </div>

          {company.palavras_chave && company.palavras_chave.length > 0 && (
            <div>
              <span className="font-medium text-gray-700 flex items-center gap-1 mb-2">
                <Tag className="h-4 w-4" />
                Itens:
              </span>
              <div className="flex flex-wrap gap-1">
                {company.palavras_chave.slice(0, 5).map((keyword, index) => (
                  <span
                    key={index}
                    className="inline-block px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs"
                  >
                    {keyword}
                  </span>
                ))}
                {company.palavras_chave.length > 5 && (
                  <span className="inline-block px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs">
                    +{company.palavras_chave.length - 5} mais
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default CompanyCard; 