import React, { useState, useEffect } from 'react';
import { ChevronDownIcon, RefreshCwIcon } from 'lucide-react';
import { apiService, Model } from '../services/api';

interface ModelPickerProps {
  onModelSelect: (modelId: string) => void;
}

export const ModelPicker: React.FC<ModelPickerProps> = ({
  onModelSelect
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const fetchModels = async (showRefreshIndicator = false) => {
    try {
      if (showRefreshIndicator) {
        setIsRefreshing(true);
      } else {
        setIsLoading(true);
      }
      
      const fetchedModels = await apiService.fetchModels();
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

  if (isLoading) {
    return (
      <div className="relative">
        <div className="w-full px-4 py-3 bg-white dark:bg-dark-card border border-gray-300 dark:border-dark-border rounded-lg">
          <div className="flex items-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-500 mr-3"></div>
            <span className="text-gray-500 dark:text-gray-400">Loading models...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!selectedModel || models.length === 0) {
    return (
      <div className="relative">
        <div className="w-full px-4 py-3 bg-white dark:bg-dark-card border border-gray-300 dark:border-dark-border rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-gray-500 dark:text-gray-400">No models available</span>
            <button 
              onClick={handleRefresh}
              className="p-1 text-gray-500 hover:text-primary-500 transition-colors"
              disabled={isRefreshing}
            >
              <RefreshCwIcon className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return <div className="relative">
      <button onClick={() => setIsOpen(!isOpen)} className="w-full flex items-center justify-between px-4 py-3 bg-white dark:bg-dark-card border border-gray-300 dark:border-dark-border rounded-lg shadow-soft hover:border-gray-400 dark:hover:border-gray-600 transition-all duration-200">
        <div className="flex items-center">
          <div className="mr-3 w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
            <span className="text-primary-700 dark:text-primary-300 text-sm font-medium">
              {selectedModel.name.substring(0, 2)}
            </span>
          </div>
          <div className="text-left">
            <p className="font-medium text-gray-800 dark:text-gray-200">
              {selectedModel.name}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {selectedModel.description}
            </p>
          </div>
        </div>
        <div className="flex items-center">
          <button 
            onClick={(e) => {
              e.stopPropagation();
              handleRefresh();
            }}
            className="mr-2 p-1 text-gray-500 hover:text-primary-500 transition-colors"
            disabled={isRefreshing}
          >
            <RefreshCwIcon className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
          <ChevronDownIcon className={`w-5 h-5 text-gray-500 transition-transform duration-200 ${isOpen ? 'transform rotate-180' : ''}`} />
        </div>
      </button>
      {isOpen && <div className="absolute mt-2 w-full bg-white dark:bg-dark-card border border-gray-200 dark:border-dark-border rounded-lg shadow-soft-lg z-10">
          <ul>
            {models.map(model => <li key={model.id}>
                <button onClick={() => handleModelSelect(model)} className={`w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors duration-150 flex items-center ${selectedModel?.id === model.id ? 'bg-primary-50 dark:bg-primary-900/20' : ''}`}>
                  <div className="mr-3 w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                    <span className="text-primary-700 dark:text-primary-300 text-sm font-medium">
                      {model.name.substring(0, 2)}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium text-gray-800 dark:text-gray-200">
                      {model.name}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {model.description}
                    </p>
                  </div>
                </button>
              </li>)}
          </ul>
        </div>}
    </div>;
};