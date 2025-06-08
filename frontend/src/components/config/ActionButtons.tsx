import React from 'react';
import { Loader2, RefreshCw } from 'lucide-react';
import { Button } from '../ui/button';
import { Status } from '../../types';

interface ActionButtonsProps {
  status: {
    daily_bids: Status;
    reevaluate: Status;
  } | null;
  loading: { [key: string]: boolean };
  onSearchNewBids: () => void;
  onReevaluateBids: () => void;
}

const ActionButtons: React.FC<ActionButtonsProps> = ({
  status,
  loading,
  onSearchNewBids,
  onReevaluateBids
}) => {
  return (
    <div className="flex gap-4">
      <Button 
        onClick={onSearchNewBids}
        disabled={status?.daily_bids.running || loading.search}
        className="flex items-center gap-2"
        size="lg"
      >
        {status?.daily_bids.running || loading.search ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <RefreshCw className="h-4 w-4" />
        )}
        Buscar Novas Licitações
      </Button>
      
      <Button 
        onClick={onReevaluateBids}
        disabled={status?.reevaluate.running || loading.reevaluate}
        variant="secondary"
        className="flex items-center gap-2"
        size="lg"
      >
        {status?.reevaluate.running || loading.reevaluate ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <RefreshCw className="h-4 w-4" />
        )}
        Reavaliar Licitações
      </Button>
    </div>
  );
};

export default ActionButtons; 