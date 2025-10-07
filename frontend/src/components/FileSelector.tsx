import React, { useState } from 'react';
import { FileIcon, UploadIcon, XIcon } from 'lucide-react';
interface FileSelectorProps {
  onFileSelect: (file: File | null) => void;
}
export const FileSelector: React.FC<FileSelectorProps> = ({
  onFileSelect
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] || null;
    setSelectedFile(file);
    onFileSelect(file);
  };
  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(true);
  };
  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
  };
  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    const file = event.dataTransfer.files?.[0] || null;
    setSelectedFile(file);
    onFileSelect(file);
  };
  const clearFile = () => {
    setSelectedFile(null);
    onFileSelect(null);
  };
  return <div className="w-full">
      <div className={`border-2 border-dashed rounded-xl p-6 transition-all duration-200 flex flex-col items-center justify-center cursor-pointer
          ${isDragging ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/10' : 'border-gray-300 dark:border-dark-border hover:border-primary-400 dark:hover:border-primary-600'}
          dark:bg-dark-card`} onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}>
        {!selectedFile ? <>
            <UploadIcon className="w-12 h-12 text-gray-400 dark:text-gray-500 mb-4" />
            <p className="text-lg font-medium text-gray-700 dark:text-gray-300">
              Drag and drop your Markdown file here
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">or</p>
            <label className="mt-4">
              <input type="file" className="hidden" accept=".md,.txt,.markdown" onChange={handleFileChange} />
              <span className="bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-lg transition-colors duration-200 cursor-pointer">
                Browse files
              </span>
            </label>
          </> : <div className="w-full">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <FileIcon className="w-10 h-10 text-primary-500 mr-3" />
                <div>
                  <p className="text-lg font-medium text-gray-800 dark:text-gray-200">
                    {selectedFile.name}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {(selectedFile.size / 1024).toFixed(2)} KB •{' '}
                    {selectedFile.type || 'Markdown'}
                  </p>
                </div>
              </div>
              <button onClick={clearFile} className="p-2 text-gray-500 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-full transition-colors" title="Remove file">
                <XIcon className="w-5 h-5" />
              </button>
            </div>
          </div>}
      </div>
    </div>;
};