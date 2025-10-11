import React, { useState } from 'react';
import { TrashIcon, CheckCircleIcon } from 'lucide-react';
interface PreviewWindowProps {
  originalText: string;
  processedText: string;
  onDelete: () => void;
}
export const PreviewWindow: React.FC<PreviewWindowProps> = ({
  originalText,
  processedText,
  onDelete
}) => {
  const [activeTab, setActiveTab] = useState<'original' | 'processed'>('processed');
  return <div className="w-full h-full bg-light-mantle dark:bg-catppuccin-mantle border border-light-surface0 dark:border-catppuccin-surface0 rounded-lg overflow-hidden flex flex-col">
      <div className="flex border-b border-light-surface0 dark:border-catppuccin-surface0">
        <button onClick={() => setActiveTab('original')} className={`px-3 py-1.5 text-sm font-medium flex-1 ${activeTab === 'original' ? 'bg-light-mantle dark:bg-catppuccin-mantle text-primary-600 dark:text-catppuccin-blue border-b-2 border-primary-500 dark:border-catppuccin-blue' : 'text-light-subtext1 dark:text-catppuccin-subtext1 hover:text-light-text dark:hover:text-catppuccin-text hover:bg-light-surface0 dark:hover:bg-catppuccin-surface0'}`}>
          Original Text
        </button>
        <button onClick={() => setActiveTab('processed')} className={`px-3 py-1.5 text-sm font-medium flex-1 ${activeTab === 'processed' ? 'bg-light-mantle dark:bg-catppuccin-mantle text-primary-600 dark:text-catppuccin-blue border-b-2 border-primary-500 dark:border-catppuccin-blue' : 'text-light-subtext1 dark:text-catppuccin-subtext1 hover:text-light-text dark:hover:text-catppuccin-text hover:bg-light-surface0 dark:hover:bg-catppuccin-surface0'}`}>
          Processed Text
        </button>
      </div>
      <div className="flex-1 overflow-auto p-3">
        {activeTab === 'original' ? <div className="prose dark:prose-invert max-w-none">
            <div className="whitespace-pre-wrap break-all overflow-hidden text-sm text-light-text dark:text-catppuccin-text font-mono">
              {originalText || 'No original text loaded.'}
            </div>
          </div> : <div className="prose dark:prose-invert max-w-none">
            <div className="whitespace-pre-wrap break-all overflow-hidden text-sm text-light-text dark:text-catppuccin-text font-mono">
              {processedText || 'No processed text available. Process a file to see results.'}
            </div>
          </div>}
      </div>
      <div className="p-2 border-t border-light-surface0 dark:border-catppuccin-surface0 flex justify-between items-center bg-light-crust dark:bg-catppuccin-crust">
        <div className="flex items-center">
          {processedText && <div className="flex items-center text-sm text-catppuccin-green dark:text-catppuccin-green">
              <CheckCircleIcon className="w-4 h-4 mr-1" />
              <span>Processing complete</span>
            </div>}
        </div>
        <div>
          <button onClick={onDelete} className="px-3 py-1.5 text-sm bg-catppuccin-red/10 dark:bg-catppuccin-red/20 text-catppuccin-red dark:text-catppuccin-red hover:bg-catppuccin-red/20 dark:hover:bg-catppuccin-red/30 rounded-lg flex items-center transition-colors" title="Clear preview">
            <TrashIcon className="w-4 h-4 mr-1.5" />
            Clear
          </button>
        </div>
      </div>
    </div>;
};