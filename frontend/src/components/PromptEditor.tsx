import React, { useState } from 'react';
import { XIcon, SaveIcon } from 'lucide-react';
interface PromptEditorProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (prompt: string) => void;
  initialPrompt: string;
}
export const PromptEditor: React.FC<PromptEditorProps> = ({
  isOpen,
  onClose,
  onSave,
  initialPrompt
}) => {
  const [prompt, setPrompt] = useState<string>(initialPrompt);
  const handleSave = () => {
    onSave(prompt);
    onClose();
  };
  if (!isOpen) return null;
  return <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-dark-card rounded-xl shadow-soft-lg w-full max-w-2xl max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-dark-border">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
            Edit Prompt Template
          </h2>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors" aria-label="Close">
            <XIcon className="w-5 h-5 text-gray-500" />
          </button>
        </div>
        <div className="p-4 flex-grow overflow-auto">
          <div className="mb-4">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
              Customize the prompt that will be sent to the LLM for processing
              your text. Use {'{text}'} as a placeholder for your document
              content.
            </p>
          </div>
          <textarea value={prompt} onChange={e => setPrompt(e.target.value)} className="w-full h-64 p-3 border border-gray-300 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-dark-background dark:text-gray-200 resize-none" placeholder="Enter your prompt template here..." />
          <div className="mt-4">
            <h3 className="font-medium text-gray-700 dark:text-gray-300 mb-2">
              Available Variables:
            </h3>
            <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
              <li>
                <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">
                  {'{text}'}
                </code>{' '}
                - The content of your document
              </li>
              <li>
                <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">
                  {'{filename}'}
                </code>{' '}
                - The name of the file
              </li>
              <li>
                <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">
                  {'{word_count}'}
                </code>{' '}
                - Total word count
              </li>
            </ul>
          </div>
        </div>
        <div className="p-4 border-t border-gray-200 dark:border-dark-border flex justify-end">
          <button onClick={onClose} className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg mr-2 transition-colors">
            Cancel
          </button>
          <button onClick={handleSave} className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg flex items-center transition-colors">
            <SaveIcon className="w-4 h-4 mr-2" />
            Save Prompt
          </button>
        </div>
      </div>
    </div>;
};