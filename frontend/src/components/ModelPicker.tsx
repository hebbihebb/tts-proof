import React, { useState, useEffect } from 'react';
import { ChevronDownIcon, RefreshCwIcon, EditIcon } from 'lucide-react';
import { apiService, Model } from '../services/api';
import { EndpointConfig } from './EndpointConfig';

interface ModelPickerProps {
  onModelSelect: (modelId: string) => void;
  onEndpointChange?: (endpoint: string) => void;
  currentEndpoint?: string;
}

export const ModelPicker: React.FC<ModelPickerProps> = ({
  onModelSelect,
  onEndpointChange,
  currentEndpoint = 'http://127.0.0.1:1234/v1'
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isEndpointConfigOpen, setIsEndpointConfigOpen] = useState<boolean>(false);

  const fetchModels = async (showRefreshIndicator = false) => {
    try {
      if (showRefreshIndicator) {
        setIsRefreshing(true);
      } else {
        setIsLoading(true);
      }
      
      const fetchedModels = await apiService.fetchModels(currentEndpoint);
      setModels(fetchedModels);
      
      if (!selectedModel && fetchedModels.length > 0) {
        const defaultModel = fetchedModels[0];
        setSelectedModel(defaultModel);
        onModelSelect(defaultModel.id);
      }
    } catch (error) {
      console.error('Failed to fetch models:', error);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);
  const handleModelSelect = (model: Model) => {
    setSelectedModel(model);
    onModelSelect(model.id);
    setIsOpen(false);
  };

  const handleRefresh = () => {
    fetchModels(true);
  };

  const handleEndpointChange = (newEndpoint: string) => {
    if (onEndpointChange) {
      onEndpointChange(newEndpoint);
      // Refresh models with new endpoint
      fetchModels(true);
    }
  };

  if (isLoading) {
    return (
      <div className="relative">
        <div className="w-full px-4 py-3 bg-light-mantle dark:bg-catppuccin-mantle border border-light-surface0 dark:border-catppuccin-surface0 rounded-lg">
          <div className="flex items-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-500 dark:border-catppuccin-blue mr-3"></div>
            <span className="text-light-subtext1 dark:text-catppuccin-subtext1">Loading models...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!selectedModel || models.length === 0) {
    return (
      <div className="relative">
        <div className="w-full px-4 py-3 bg-light-mantle dark:bg-catppuccin-mantle border border-light-surface0 dark:border-catppuccin-surface0 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-light-subtext1 dark:text-catppuccin-subtext1">No models available</span>
            <div className="flex items-center">
              <button 
                onClick={() => setIsEndpointConfigOpen(true)}
                className="mr-2 p-1 text-light-subtext1 dark:text-catppuccin-subtext1 hover:text-primary-500 dark:hover:text-catppuccin-blue transition-colors"
                title="Configure API Endpoint"
              >
                <EditIcon className="w-4 h-4" />
              </button>
              <button 
                onClick={handleRefresh}
                className="p-1 text-light-subtext1 dark:text-catppuccin-subtext1 hover:text-primary-500 dark:hover:text-catppuccin-blue transition-colors"
                disabled={isRefreshing}
                title="Refresh Models"
              >
                <RefreshCwIcon className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
        </div>
        
        <EndpointConfig
          isOpen={isEndpointConfigOpen}
          onClose={() => setIsEndpointConfigOpen(false)}
          currentEndpoint={currentEndpoint}
          onEndpointChange={handleEndpointChange}
        />
      </div>
    );
  }

  return <div className="relative">
      <button onClick={() => setIsOpen(!isOpen)} className="w-full flex items-center justify-between px-4 py-3 bg-light-mantle dark:bg-catppuccin-mantle border border-light-surface0 dark:border-catppuccin-surface0 rounded-lg shadow-soft hover:border-light-surface1 dark:hover:border-catppuccin-surface1 transition-all duration-200">
        <div className="flex items-center">
          <div className="mr-3 w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
            <span className="text-primary-700 dark:text-primary-300 text-sm font-medium">
              {selectedModel.name.substring(0, 2)}
            </span>
          </div>
          <div className="text-left">
            <p className="font-medium text-light-text dark:text-catppuccin-text">
              {selectedModel.name}
            </p>
            <p className="text-sm text-light-subtext1 dark:text-catppuccin-subtext1">
              {selectedModel.description}
            </p>
            <p className="text-xs text-light-subtext0 dark:text-catppuccin-subtext0 mt-1">
              Endpoint: {new URL(currentEndpoint).host}
            </p>
          </div>
        </div>
        <div className="flex items-center">
          <button 
            onClick={(e) => {
              e.stopPropagation();
              setIsEndpointConfigOpen(true);
            }}
            className="mr-2 p-1 text-light-subtext1 dark:text-catppuccin-subtext1 hover:text-primary-500 dark:hover:text-catppuccin-blue transition-colors"
            title="Configure API Endpoint"
          >
            <EditIcon className="w-4 h-4" />
          </button>
          <button 
            onClick={(e) => {
              e.stopPropagation();
              handleRefresh();
            }}
            className="mr-2 p-1 text-light-subtext1 dark:text-catppuccin-subtext1 hover:text-primary-500 dark:hover:text-catppuccin-blue transition-colors"
            disabled={isRefreshing}
            title="Refresh Models"
          >
            <RefreshCwIcon className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
          <ChevronDownIcon className={`w-5 h-5 text-light-subtext1 dark:text-catppuccin-subtext1 transition-transform duration-200 ${isOpen ? 'transform rotate-180' : ''}`} />
        </div>
      </button>
      {isOpen && <div className="absolute mt-2 w-full bg-light-mantle dark:bg-catppuccin-mantle border border-light-surface0 dark:border-catppuccin-surface0 rounded-lg shadow-soft-lg z-10">
          <ul>
            {models.map(model => <li key={model.id}>
                <button onClick={() => handleModelSelect(model)} className={`w-full text-left px-4 py-3 hover:bg-light-surface0 dark:hover:bg-catppuccin-surface0 transition-colors duration-150 flex items-center ${selectedModel?.id === model.id ? 'bg-primary-50 dark:bg-catppuccin-blue/20' : ''}`}>
                  <div className="mr-3 w-8 h-8 rounded-full bg-primary-100 dark:bg-catppuccin-blue/30 flex items-center justify-center">
                    <span className="text-primary-700 dark:text-catppuccin-blue text-sm font-medium">
                      {model.name.substring(0, 2)}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium text-light-text dark:text-catppuccin-text">
                      {model.name}
                    </p>
                    <p className="text-sm text-light-subtext1 dark:text-catppuccin-subtext1">
                      {model.description}
                    </p>
                  </div>
                </button>
              </li>)}
          </ul>
        </div>}
      
      <EndpointConfig
        isOpen={isEndpointConfigOpen}
        onClose={() => setIsEndpointConfigOpen(false)}
        currentEndpoint={currentEndpoint}
        onEndpointChange={handleEndpointChange}
      />
    </div>;
};