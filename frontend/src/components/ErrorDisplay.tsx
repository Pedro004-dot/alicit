import React from 'react';
import { AlertCircle } from 'lucide-react';
import { Card, CardContent } from './ui/card';

interface ErrorDisplayProps {
  error: string | null;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ error }) => {
  if (!error) return null;

  return (
    <Card className="border-red-200 bg-red-50">
      <CardContent className="pt-6">
        <div className="flex items-center gap-2 text-red-800">
          <AlertCircle className="h-5 w-5" />
          <span className="font-medium">Erro:</span>
          <span>{error}</span>
        </div>
      </CardContent>
    </Card>
  );
};

export default ErrorDisplay; 