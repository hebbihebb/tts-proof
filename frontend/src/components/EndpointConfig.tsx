import React, { useState, useEffect } from 'react';
import { XIcon, ServerIcon, WifiIcon, GlobeIcon } from 'lucide-react';

interface EndpointConfigProps {
  isOpen: boolean;
  onClose: () => void;
  currentEndpoint: string;
  onEndpointChange: (endpoint: string) => void;
}

interface PresetEndpoint {
  name: string;
  url: string;
  description: string;
  icon: React.ReactNode;
}

const PRESET_ENDPOINTS: PresetEndpoint[] = [
  {
    name: 'LM Studio (Local)',
    url: 'http://127.0.0.1:1234/v1',
    description: 'Default LM Studio local server',
    icon: <ServerIcon className="w-4 h-4" />
  },
  {
    name: 'LM Studio (Alt Port)',
    url: 'http://127.0.0.1:1235/v1',
    description: 'LM Studio on alternative port',
    icon: <ServerIcon className="w-4 h-4" />
  },
  {
    name: 'KoboldCpp',
    url: 'http://127.0.0.1:5001/v1',
    description: 'Local KoboldCpp server',
    icon: <WifiIcon className="w-4 h-4" />
  },
  {
    name: 'Oobabooga Text-gen',
    url: 'http://127.0.0.1:5000/v1',
    description: 'Text-generation-webui server',
    icon: <WifiIcon className="w-4 h-4" />
  },
  {
    name: 'TabbyAPI',
    url: 'http://127.0.0.1:5000/v1',
    description: 'TabbyAPI server',
    icon: <WifiIcon className="w-4 h-4" />
  }
];

export const EndpointConfig: React.FC<EndpointConfigProps> = ({
  isOpen,
  onClose,
  currentEndpoint,
  onEndpointChange
}) => {
  const [selectedMode, setSelectedMode] = useState<'preset' | 'custom'>('preset');
  const [customEndpoint, setCustomEndpoint] = useState('');
  const [customHost, setCustomHost] = useState('127.0.0.1');
  const [customPort, setCustomPort] = useState('1234');
  const [selectedPreset, setSelectedPreset] = useState<string>('');
  const [activeInput, setActiveInput] = useState<'hostport' | 'fullurl'>('hostport');

  useEffect(() => {
    if (isOpen) {
      // Initialize based on current endpoint
      const preset = PRESET_ENDPOINTS.find(p => p.url === currentEndpoint);
      if (preset) {
        setSelectedMode('preset');
        setSelectedPreset(preset.url);
        setActiveInput('hostport'); // Default for presets
      } else {
        setSelectedMode('custom');
        setCustomEndpoint(currentEndpoint);
        
        // Try to parse host and port from current endpoint
        try {
          const url = new URL(currentEndpoint);
          setCustomHost(url.hostname);
          setCustomPort(url.port || '1234');
          setActiveInput('hostport'); // Start with host/port for parsing
        } catch (e) {
          // Invalid URL, keep defaults and use full URL mode
          setActiveInput('fullurl');
        }
      }
    }
  }, [isOpen, currentEndpoint]);

  const handleSave = () => {
    if (selectedMode === 'preset' && selectedPreset) {
      onEndpointChange(selectedPreset);
    } else if (selectedMode === 'custom') {
      if (activeInput === 'fullurl' && customEndpoint.trim()) {
        // User entered full URL
        onEndpointChange(customEndpoint.trim());
      } else {
        // Use host/port builder
        const endpoint = `http://${customHost}:${customPort}/v1`;
        onEndpointChange(endpoint);
      }
    }
    onClose();
  };

  const handlePresetSelect = (url: string) => {
    setSelectedPreset(url);
  };

  const buildCustomEndpoint = () => {
    return `http://${customHost}:${customPort}/v1`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-light-mantle dark:bg-catppuccin-mantle rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-light-surface0 dark:border-catppuccin-surface0">
          <h2 className="text-xl font-semibold text-light-text dark:text-catppuccin-text">
            Configure API Endpoint
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-light-surface0 dark:hover:bg-catppuccin-surface0 rounded-lg transition-colors"
          >
            <XIcon className="w-5 h-5 text-light-subtext1 dark:text-catppuccin-subtext1" />
          </button>
        </div>

        <div className="p-6">
          {/* Mode Selection */}
          <div className="mb-6">
            <div className="flex space-x-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
              <button
                onClick={() => setSelectedMode('preset')}
                className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                  selectedMode === 'preset'
                    ? 'bg-light-mantle dark:bg-catppuccin-mantle text-primary-600 dark:text-catppuccin-blue shadow-sm'
                    : 'text-light-subtext1 dark:text-catppuccin-subtext1 hover:text-light-text dark:hover:text-catppuccin-text'
                }`}
              >
                <ServerIcon className="w-4 h-4 inline mr-2" />
                Presets
              </button>
              <button
                onClick={() => setSelectedMode('custom')}
                className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                  selectedMode === 'custom'
                    ? 'bg-light-mantle dark:bg-catppuccin-mantle text-primary-600 dark:text-catppuccin-blue shadow-sm'
                    : 'text-light-subtext1 dark:text-catppuccin-subtext1 hover:text-light-text dark:hover:text-catppuccin-text'
                }`}
              >
                <GlobeIcon className="w-4 h-4 inline mr-2" />
                Custom
              </button>
            </div>
          </div>

          {/* Preset Mode */}
          {selectedMode === 'preset' && (
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-light-text dark:text-catppuccin-text mb-3">
                Select a preset endpoint:
              </h3>
              {PRESET_ENDPOINTS.map((preset) => (
                <div
                  key={preset.url}
                  onClick={() => handlePresetSelect(preset.url)}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    selectedPreset === preset.url
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-light-surface0 dark:border-catppuccin-surface0 hover:border-light-surface1 dark:hover:border-catppuccin-surface1'
                  }`}
                >
                  <div className="flex items-start">
                    <div className="mr-3 mt-1">
                      {preset.icon}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium text-light-text dark:text-catppuccin-text">
                          {preset.name}
                        </h4>
                        <code className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
                          {preset.url}
                        </code>
                      </div>
                      <p className="text-sm text-light-subtext1 dark:text-catppuccin-subtext1 mt-1">
                        {preset.description}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Custom Mode */}
          {selectedMode === 'custom' && (
            <div className="space-y-4">
              <h3 className="text-sm font-medium text-light-text dark:text-catppuccin-text">
                Custom endpoint configuration:
              </h3>
              
              {/* Quick Host/Port Builder */}
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                <h4 className="text-sm font-medium text-light-text dark:text-catppuccin-text mb-3">
                  Quick Setup
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-light-subtext1 dark:text-catppuccin-subtext1 mb-1">
                      Host/IP Address
                    </label>
                    <input
                      type="text"
                      value={customHost}
                      onChange={(e) => {
                        setCustomHost(e.target.value);
                        setActiveInput('hostport');
                      }}
                      placeholder="127.0.0.1 or 192.168.1.100"
                      className="w-full px-3 py-2 border border-light-surface1 dark:border-catppuccin-surface1 rounded-md bg-light-base dark:bg-catppuccin-base text-light-text dark:text-catppuccin-text text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-light-subtext1 dark:text-catppuccin-subtext1 mb-1">
                      Port
                    </label>
                    <input
                      type="text"
                      value={customPort}
                      onChange={(e) => {
                        setCustomPort(e.target.value);
                        setActiveInput('hostport');
                      }}
                      placeholder="1234"
                      className="w-full px-3 py-2 border border-light-surface1 dark:border-catppuccin-surface1 rounded-md bg-light-base dark:bg-catppuccin-base text-light-text dark:text-catppuccin-text text-sm"
                    />
                  </div>
                </div>
                <div className="mt-3 p-2 bg-light-base dark:bg-catppuccin-base rounded border border-light-surface1 dark:border-catppuccin-surface1">
                  <span className="text-xs text-light-subtext0 dark:text-catppuccin-subtext0">Preview: </span>
                  <code className="text-xs text-primary-600 dark:text-primary-400">
                    {buildCustomEndpoint()}
                  </code>
                </div>
              </div>

              {/* Full URL Input */}
              <div>
                <label className="block text-sm font-medium text-light-text dark:text-catppuccin-text mb-2">
                  Or enter full endpoint URL:
                </label>
                <input
                  type="text"
                  value={customEndpoint}
                  onChange={(e) => {
                    setCustomEndpoint(e.target.value);
                    setActiveInput('fullurl');
                  }}
                  placeholder="http://192.168.1.100:1234/v1"
                  className="w-full px-3 py-2 border border-light-surface1 dark:border-catppuccin-surface1 rounded-md bg-light-base dark:bg-catppuccin-base text-light-text dark:text-catppuccin-text"
                />
                <p className="text-xs text-light-subtext0 dark:text-catppuccin-subtext0 mt-1">
                  Must be OpenAI-compatible API endpoint (usually ends with /v1)
                </p>
              </div>
            </div>
          )}

          {/* Test Connection */}
          <div className="mt-6">
            <button
              onClick={async () => {
                const testEndpoint = selectedMode === 'preset' ? selectedPreset : 
                  (activeInput === 'fullurl' && customEndpoint.trim()) ? customEndpoint.trim() : 
                  `http://${customHost}:${customPort}/v1`;
                
                try {
                  const response = await fetch(`http://localhost:8000/api/test-endpoint?api_base=${encodeURIComponent(testEndpoint)}&model=default`);
                  const result = await response.json();
                  
                  if (result.status === 'success') {
                    alert(`✅ Connection successful!\n\nModels available: ${result.models_available}\nChat endpoint: ${result.chat_working ? 'Working' : 'Not working'}\nTest response: "${result.test_response}"`);
                  } else {
                    alert(`❌ Connection failed:\n${result.error}`);
                  }
                } catch (error) {
                  alert(`❌ Test failed: ${error}`);
                }
              }}
              className="w-full py-2 px-4 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors text-sm"
            >
              Test Connection
            </button>
          </div>

          {/* Current Endpoint Display */}
          <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <p className="text-xs text-blue-600 dark:text-blue-400 font-medium">
              Current endpoint: <code className="bg-blue-100 dark:bg-blue-900/40 px-1 rounded">{currentEndpoint}</code>
            </p>
          </div>
        </div>

        <div className="flex justify-end space-x-3 p-6 border-t border-light-surface0 dark:border-catppuccin-surface0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-light-subtext1 dark:text-catppuccin-subtext1 hover:text-light-text dark:hover:text-catppuccin-text transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors"
          >
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
};