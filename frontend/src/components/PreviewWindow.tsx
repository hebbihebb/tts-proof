import React, { useState } from 'react';
import { TrashIcon, CheckCircleIcon, XCircleIcon } from 'lucide-react';
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
  return <div className="w-full h-full bg-white dark:bg-dark-card border border-gray-200 dark:border-dark-border rounded-lg overflow-hidden flex flex-col">
      <div className="flex border-b border-gray-200 dark:border-dark-border">
        <button onClick={() => setActiveTab('original')} className={`px-4 py-2 text-sm font-medium flex-1 ${activeTab === 'original' ? 'bg-white dark:bg-dark-card text-primary-600 dark:text-primary-400 border-b-2 border-primary-500' : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800'}`}>
          Original Text
        </button>
        <button onClick={() => setActiveTab('processed')} className={`px-4 py-2 text-sm font-medium flex-1 ${activeTab === 'processed' ? 'bg-white dark:bg-dark-card text-primary-600 dark:text-primary-400 border-b-2 border-primary-500' : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800'}`}>
          Processed Text
        </button>
      </div>
      <div className="flex-1 overflow-auto p-4">
        {activeTab === 'original' ? <div className="prose dark:prose-invert max-w-none">
            <pre className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200">
              {originalText || 'No original text loaded.'}
            </pre>
          </div> : <div className="prose dark:prose-invert max-w-none">
            <pre className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200">
              {processedText || 'No processed text available. Process a file to see results.'}
            </pre>
          </div>}
      </div>
      <div className="p-3 border-t border-gray-200 dark:border-dark-border flex justify-between items-center bg-gray-50 dark:bg-dark-background">
        <div className="flex items-center">
          {processedText && <div className="flex items-center text-sm text-green-600 dark:text-green-400">
              <CheckCircleIcon className="w-4 h-4 mr-1" />
              <span>Processing complete</span>
            </div>}
        </div>
        <div>
          <button onClick={onDelete} className="px-3 py-1.5 text-sm bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg flex items-center transition-colors" title="Clear preview">
            <TrashIcon className="w-4 h-4 mr-1.5" />
            Clear
          </button>
        </div>
      </div>
    </div>;
};