import React, { useState, useEffect } from 'react';
import { Upload, CheckCircle, AlertCircle, Database } from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

interface Stats {
  opportunities?: number;
  researchers?: number;
  proposals?: number;
}

const DataIngestion: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | null; text: string }>({
    type: null,
    text: '',
  });
  const [stats, setStats] = useState<Stats>({});
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/stats`);
      if (response.data.success) {
        setStats(response.data.stats);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

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

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    const csvFile = files.find(f => f.name.endsWith('.csv'));
    
    if (csvFile) {
      setFile(csvFile);
      setMessage({ type: null, text: '' });
    } else {
      setMessage({ type: 'error', text: 'Please drop a CSV file' });
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setMessage({ type: null, text: '' });
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage({ type: 'error', text: 'Please select a file first' });
      return;
    }

    setUploading(true);
    setMessage({ type: null, text: '' });

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE}/ingest/csv`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        setMessage({
          type: 'success',
          text: `Successfully processed ${response.data.filename}. ${response.data.message}`,
        });
        setFile(null);
        // Refresh stats
        fetchStats();
      } else {
        setMessage({ type: 'error', text: response.data.error || 'Upload failed' });
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'Failed to upload file. Please ensure the server is running.',
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Data Ingestion</h2>
        <p className="mt-2 text-gray-600">
          Upload CSV files containing funding opportunities. The system will automatically
          process new entries, create embeddings, and store them in the database.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Opportunities</p>
              <p className="text-2xl font-bold text-gray-900">{stats.opportunities || 0}</p>
            </div>
            <Database className="h-8 w-8 text-indigo-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Researchers</p>
              <p className="text-2xl font-bold text-gray-900">{stats.researchers || 0}</p>
            </div>
            <Database className="h-8 w-8 text-green-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Proposals</p>
              <p className="text-2xl font-bold text-gray-900">{stats.proposals || 0}</p>
            </div>
            <Database className="h-8 w-8 text-purple-600" />
          </div>
        </div>
      </div>

      {/* Upload Area */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload CSV File</h3>
          
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
              Drag and drop a CSV file here, or click to select
            </p>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className="mt-4 inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 cursor-pointer"
            >
              Select CSV File
            </label>
          </div>

          {file && (
            <div className="mt-4 flex items-center justify-between bg-gray-50 rounded-lg p-4">
              <div className="flex items-center">
                <Database className="h-5 w-5 text-gray-400 mr-2" />
                <span className="text-sm text-gray-900">{file.name}</span>
                <span className="ml-2 text-sm text-gray-500">
                  ({(file.size / 1024).toFixed(2)} KB)
                </span>
              </div>
              <button
                onClick={() => setFile(null)}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Remove
              </button>
            </div>
          )}

          {message.text && (
            <div
              className={`mt-4 p-4 rounded-lg flex items-start ${
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

          <div className="mt-6">
            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className={`w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
                !file || uploading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-indigo-600 hover:bg-indigo-700'
              }`}
            >
              {uploading ? 'Processing...' : 'Upload and Process'}
            </button>
          </div>
        </div>
      </div>

      {/* Instructions */}
      <div className="bg-blue-50 rounded-lg p-6">
        <h4 className="text-sm font-semibold text-blue-900 mb-2">CSV Format Requirements</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Required columns: title, description, url, agency, keywords</li>
          <li>• Date columns: close_date, due_date, or deadline</li>
          <li>• Keywords should be comma-separated values</li>
          <li>• The system automatically handles duplicate entries</li>
          <li>• Expired opportunities are automatically removed</li>
        </ul>
      </div>
    </div>
  );
};

export default DataIngestion;