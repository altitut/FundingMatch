import React, { useState } from 'react';
import { Upload, FileText, Link, CheckCircle, AlertCircle, Plus, X } from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

interface UploadedFile {
  filename: string;
  path: string;
  type: 'pdf' | 'json';
}

const UserProfile: React.FC = () => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [urls, setUrls] = useState<string[]>(['']);
  const [name, setName] = useState('');
  const [interests, setInterests] = useState('');
  const [uploading, setUploading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | null; text: string }>({
    type: null,
    text: '',
  });
  const [isDragging, setIsDragging] = useState(false);

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    for (const file of droppedFiles) {
      if (file.name.endsWith('.pdf') || file.name.endsWith('.json')) {
        await uploadFile(file);
      }
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (selectedFiles) {
      for (let i = 0; i < selectedFiles.length; i++) {
        await uploadFile(selectedFiles[i]);
      }
    }
  };

  const uploadFile = async (file: File) => {
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE}/profile/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        const fileType = file.name.endsWith('.pdf') ? 'pdf' : 'json';
        setFiles([...files, {
          filename: response.data.filename,
          path: response.data.path,
          type: fileType,
        }]);
      }
    } catch (error) {
      setMessage({ type: 'error', text: `Failed to upload ${file.name}` });
    } finally {
      setUploading(false);
    }
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const addUrlField = () => {
    setUrls([...urls, '']);
  };

  const updateUrl = (index: number, value: string) => {
    const newUrls = [...urls];
    newUrls[index] = value;
    setUrls(newUrls);
  };

  const removeUrl = (index: number) => {
    setUrls(urls.filter((_, i) => i !== index));
  };

  const handleCreateProfile = async () => {
    if (!name.trim()) {
      setMessage({ type: 'error', text: 'Please enter your name' });
      return;
    }

    setCreating(true);
    setMessage({ type: null, text: '' });

    try {
      const response = await axios.post(`${API_BASE}/profile/create`, {
        files,
        urls: urls.filter(url => url.trim() !== ''),
        name: name.trim(),
        interests: interests.split(',').map(i => i.trim()).filter(i => i),
      });

      if (response.data.success) {
        setMessage({
          type: 'success',
          text: `Profile created successfully! ${response.data.profile.documents_processed} documents processed.`,
        });
      } else {
        setMessage({ type: 'error', text: response.data.error || 'Failed to create profile' });
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'Failed to create profile. Please ensure the server is running.',
      });
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900">User Profile</h2>
        <p className="mt-2 text-gray-600">
          Upload your CV, research papers, and provide URLs to create a comprehensive profile.
          The system will extract information to match you with relevant funding opportunities.
        </p>
      </div>

      {/* Basic Information */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Enter your full name"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Research Interests
            </label>
            <textarea
              value={interests}
              onChange={(e) => setInterests(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              rows={3}
              placeholder="Enter your research interests, separated by commas (e.g., AI, Machine Learning, Biomedical Engineering)"
            />
          </div>
        </div>
      </div>

      {/* Document Upload */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Documents</h3>
        
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            isDragging
              ? 'border-indigo-500 bg-indigo-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <Upload className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-2 text-sm text-gray-600">
            Drag and drop PDF files or JSON profile here, or click to select
          </p>
          <input
            type="file"
            accept=".pdf,.json"
            multiple
            onChange={handleFileSelect}
            className="hidden"
            id="doc-upload"
          />
          <label
            htmlFor="doc-upload"
            className="mt-4 inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 cursor-pointer"
          >
            Select Files
          </label>
        </div>

        {files.length > 0 && (
          <div className="mt-4 space-y-2">
            {files.map((file, index) => (
              <div key={index} className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
                <div className="flex items-center">
                  <FileText className="h-5 w-5 text-gray-400 mr-2" />
                  <span className="text-sm text-gray-900">{file.filename}</span>
                  <span className="ml-2 px-2 py-1 text-xs rounded-full bg-gray-200 text-gray-700">
                    {file.type.toUpperCase()}
                  </span>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="text-red-600 hover:text-red-800"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* URL Input */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Profile URLs</h3>
        <p className="text-sm text-gray-600 mb-4">
          Add links to your faculty page, Google Scholar, NSF awards, etc.
        </p>
        
        <div className="space-y-3">
          {urls.map((url, index) => (
            <div key={index} className="flex items-center space-x-2">
              <Link className="h-5 w-5 text-gray-400" />
              <input
                type="url"
                value={url}
                onChange={(e) => updateUrl(index, e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="https://example.com/your-profile"
              />
              {urls.length > 1 && (
                <button
                  onClick={() => removeUrl(index)}
                  className="text-red-600 hover:text-red-800"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          ))}
          <button
            onClick={addUrlField}
            className="flex items-center text-sm text-indigo-600 hover:text-indigo-800"
          >
            <Plus className="h-4 w-4 mr-1" />
            Add another URL
          </button>
        </div>
      </div>

      {/* Messages */}
      {message.text && (
        <div
          className={`p-4 rounded-lg flex items-start ${
            message.type === 'success'
              ? 'bg-green-50 text-green-800'
              : 'bg-red-50 text-red-800'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle className="h-5 w-5 mr-2 flex-shrink-0" />
          ) : (
            <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0" />
          )}
          <span className="text-sm">{message.text}</span>
        </div>
      )}

      {/* Create Profile Button */}
      <div>
        <button
          onClick={handleCreateProfile}
          disabled={creating || !name.trim()}
          className={`w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
            creating || !name.trim()
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-indigo-600 hover:bg-indigo-700'
          }`}
        >
          {creating ? 'Creating Profile...' : 'Create Profile'}
        </button>
      </div>

      {/* Instructions */}
      <div className="bg-blue-50 rounded-lg p-6">
        <h4 className="text-sm font-semibold text-blue-900 mb-2">Tips for Best Results</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Upload your most recent CV or resume</li>
          <li>• Include successful grant proposals if available</li>
          <li>• Add links to your faculty profile and Google Scholar</li>
          <li>• Provide detailed research interests for better matching</li>
          <li>• Include any research papers that showcase your expertise</li>
        </ul>
      </div>
    </div>
  );
};

export default UserProfile;