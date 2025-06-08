import React from 'react';
import { Cog } from 'lucide-react';
import { Button } from '../ui/button';
import { MatchingConfig, Status } from '../../types';
import VectorizerSelection from '../config/VectorizerSelection';
import AdvancedConfig from '../config/AdvancedConfig';
import ActionButtons from '../config/ActionButtons';
import ConfigSummary from '../config/ConfigSummary';
import ErrorDisplay from '../ErrorDisplay';

interface ConfigurationTabProps {
  config: MatchingConfig;
  setConfig: React.Dispatch<React.SetStateAction<MatchingConfig>>;
  showAdvancedConfig: boolean;
  setShowAdvancedConfig: React.Dispatch<React.SetStateAction<boolean>>;
  status: {
    daily_bids: Status;
    reevaluate: Status;
  } | null;
  loading: { [key: string]: boolean };
  error: string | null;
  onSearchNewBids: () => void;
  onReevaluateBids: () => void;
}

const ConfigurationTab: React.FC<ConfigurationTabProps> = ({
  config,
  setConfig,
  showAdvancedConfig,
  setShowAdvancedConfig,
  status,
  loading,
  error,
  onSearchNewBids,
  onReevaluateBids
}) => {
  return (
    <div className="space-y-6">
      {/* Vectorizer Selection */}
      <VectorizerSelection config={config} setConfig={setConfig} />

      {/* Advanced Configuration Toggle */}
      <div className="flex justify-center">
        <Button
          variant="outline"
          onClick={() => setShowAdvancedConfig(!showAdvancedConfig)}
          className="flex items-center gap-2"
        >
          <Cog className="h-4 w-4" />
          {showAdvancedConfig ? 'Ocultar' : 'Mostrar'} Configurações Avançadas
        </Button>
      </div>

      {/* Advanced Configuration Panel */}
      <AdvancedConfig 
        config={config} 
        setConfig={setConfig} 
        showAdvancedConfig={showAdvancedConfig} 
      />

      {/* Action Buttons */}
      <ActionButtons
        status={status}
        loading={loading}
        onSearchNewBids={onSearchNewBids}
        onReevaluateBids={onReevaluateBids}
      />

      {/* Current Configuration Summary */}
      <ConfigSummary config={config} />

      {/* Error Display */}
      <ErrorDisplay error={error} />
    </div>
  );
};

export default ConfigurationTab; 