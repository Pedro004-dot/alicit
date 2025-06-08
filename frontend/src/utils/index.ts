import { Award, TrendingUp, Target } from 'lucide-react';

export const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value);
};

export const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('pt-BR');
};

export const getScorePercentage = (score: number) => {
  return Math.round(score * 100);
};

export const getScoreColor = (score: number) => {
  const percentage = getScorePercentage(score);
  if (percentage >= 80) return 'text-green-600 bg-green-100';
  if (percentage >= 60) return 'text-yellow-600 bg-yellow-100';
  return 'text-red-600 bg-red-100';
};

export const getPerformanceColor = (performance: string) => {
  switch (performance) {
    case 'high': return 'bg-green-100 text-green-800';
    case 'medium': return 'bg-yellow-100 text-yellow-800';
    case 'low': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

export const getCostColor = (cost: string) => {
  switch (cost) {
    case 'free': return 'bg-blue-100 text-blue-800';
    case 'paid': return 'bg-purple-100 text-purple-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}; 