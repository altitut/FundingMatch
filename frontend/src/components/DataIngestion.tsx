import React, { useState, useEffect } from 'react';
import { Upload, CheckCircle, AlertCircle, Database, ExternalLink, Calendar, ChevronLeft, ChevronRight, Target } from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:5001/api';

interface Stats {
  opportunities?: number;
  researchers?: number;
  proposals?: number;
  high_confidence_matches?: number;
  top_matches?: Array<{
    opportunity_id: string;
    title: string;
    agency: string;
    max_score: number;
    matched_users: number;
  }>;
}

interface ProgressInfo {
  status: string;
  stage?: string;
  message?: string;
  current?: number;
  total?: number;
  summary?: any;
  error?: string;
}

interface Opportunity {
  id: string;
  title: string;
  agency: string;
  deadline: string;
  url: string;
  topic_number?: string;
}

interface UnprocessedOpportunity {
  title: string;
  agency: string;
  reason: string;
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
  const [progress, setProgress] = useState<ProgressInfo | null>(null);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [unprocessedOpportunities, setUnprocessedOpportunities] = useState<UnprocessedOpportunity[]>([]);
  const [activeTab, setActiveTab] = useState<'processed' | 'unprocessed'>('processed');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 100;

  useEffect(() => {
    fetchStats();
    fetchOpportunities();
  }, []);

  // Calculate pagination values
  const totalPages = Math.ceil(
    activeTab === 'processed' 
      ? opportunities.length / itemsPerPage 
      : unprocessedOpportunities.length / itemsPerPage
  );
  
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  
  const paginatedOpportunities = opportunities.slice(startIndex, endIndex);
  const paginatedUnprocessedOpportunities = unprocessedOpportunities.slice(startIndex, endIndex);
  
  // Reset page when switching tabs
  useEffect(() => {
    setCurrentPage(1);
  }, [activeTab]);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

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

  const fetchOpportunities = async () => {
    try {
      const response = await axios.get(`${API_BASE}/opportunities`);
      if (response.data.success) {
        setOpportunities(response.data.opportunities);
      }
    } catch (error) {
      console.error('Failed to fetch opportunities:', error);
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
    setProgress(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE}/ingest/csv`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        // Start listening to progress updates
        const sessionId = response.data.session_id;
        const eventSource = new EventSource(`${API_BASE}/ingest/progress/${sessionId}`);
        
        eventSource.onmessage = (event) => {
          const data = JSON.parse(event.data);
          
          if (data.keepalive) {
            // Ignore keepalive messages
            return;
          }
          
          setProgress(data);
          
          // Log debug messages to console
          if (data.stage === 'debug') {
            console.log('Debug:', data.message);
          }
          
          if (data.status === 'complete') {
            const summary = data.summary;
            setMessage({
              type: 'success',
              text: `Successfully processed ${summary.filename}. Added ${summary.new_opportunities} new opportunities, skipped ${summary.duplicate_skipped} duplicates and ${summary.expired_skipped} expired.`,
            });
            setFile(null);
            setProgress(null);
            setUploading(false);
            // Set unprocessed opportunities
            if (summary.unprocessed && summary.unprocessed.length > 0) {
              setUnprocessedOpportunities(summary.unprocessed);
              setActiveTab('unprocessed');
            }
            // Refresh stats and opportunities
            fetchStats();
            fetchOpportunities();
            eventSource.close();
          } else if (data.status === 'error') {
            setMessage({ type: 'error', text: data.error || 'Processing failed' });
            setProgress(null);
            setUploading(false);
            eventSource.close();
          }
        };
        
        eventSource.onerror = (error) => {
          console.error('SSE Error:', error);
          setMessage({ type: 'error', text: 'Lost connection to server' });
          setProgress(null);
          setUploading(false);
          eventSource.close();
        };
      } else {
        setMessage({ type: 'error', text: response.data.error || 'Upload failed' });
        setUploading(false);
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'Failed to upload file. Please ensure the server is running.',
      });
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
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">Total Opportunities</p>
              <p className="text-2xl font-bold text-gray-900">{stats.opportunities || 0}</p>
              <p className="text-xs text-gray-500 mt-1">Active with deadlines</p>
            </div>
            <Database className="h-8 w-8 text-indigo-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">Researchers</p>
              <p className="text-2xl font-bold text-gray-900">{stats.researchers || 0}</p>
              <p className="text-xs text-gray-500 mt-1">Active profiles</p>
            </div>
            <Database className="h-8 w-8 text-green-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">High-Confidence Matches</p>
              <p className="text-2xl font-bold text-gray-900">{stats.high_confidence_matches || 0}</p>
              <p className="text-xs text-gray-500 mt-1">Over 80% confidence</p>
            </div>
            <Target className="h-8 w-8 text-purple-600" />
          </div>
        </div>
      </div>

      {/* Top High-Confidence Matches */}
      {stats.top_matches && stats.top_matches.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top High-Confidence Matches</h3>
          <div className="space-y-3">
            {stats.top_matches.map((match, index) => (
              <div key={match.opportunity_id} className="border-l-4 border-green-500 pl-4 py-2">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-gray-900 line-clamp-1">
                      {match.title}
                    </h4>
                    <div className="mt-1 flex items-center space-x-4 text-xs text-gray-600">
                      <span>{match.agency}</span>
                      <span className="flex items-center">
                        <svg className="h-3 w-3 text-green-600 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        {match.max_score.toFixed(1)}% match
                      </span>
                      <span>{match.matched_users} researcher{match.matched_users !== 1 ? 's' : ''}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <p className="mt-4 text-xs text-gray-500">
            These opportunities have matched with researchers at over 80% confidence
          </p>
        </div>
      )}

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

          {progress && progress.status === 'processing' && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-blue-900">
                  {progress.message || 'Processing...'}
                </span>
                {progress.current && progress.total && (
                  <span className="text-sm text-blue-700">
                    {progress.current} / {progress.total}
                  </span>
                )}
              </div>
              {progress.current && progress.total && (
                <div className="w-full bg-blue-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(progress.current / progress.total) * 100}%` }}
                  />
                </div>
              )}
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

      {/* Opportunities Table */}
      {(opportunities.length > 0 || unprocessedOpportunities.length > 0) && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Funding Opportunities</h3>
              {/* Page info */}
              {totalPages > 1 && (
                <span className="text-sm text-gray-600">
                  Page {currentPage} of {totalPages} (Groups of {itemsPerPage})
                </span>
              )}
            </div>
            
            {/* Tabs */}
            <div className="border-b border-gray-200 mb-4">
              <nav className="-mb-px flex space-x-8">
                <button
                  onClick={() => setActiveTab('processed')}
                  className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'processed'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Processed ({opportunities.length})
                </button>
                <button
                  onClick={() => setActiveTab('unprocessed')}
                  className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'unprocessed'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Unprocessed ({unprocessedOpportunities.length})
                </button>
              </nav>
            </div>
            
            <div className="overflow-x-auto">
              {activeTab === 'processed' ? (
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        #
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        ID
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Title
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Agency
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Deadline
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        URL
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {paginatedOpportunities.map((opp, index) => (
                      <tr key={opp.id}>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          {startIndex + index + 1}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                          {opp.topic_number || opp.id.substring(0, 8)}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          <div className="max-w-xs truncate" title={opp.title}>
                            {opp.title}
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                          {opp.agency}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                          <div className="flex items-center">
                            <Calendar className="h-4 w-4 mr-1" />
                            {opp.deadline || 'Not specified'}
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                          {opp.url ? (
                            <a
                              href={opp.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-indigo-600 hover:text-indigo-900 flex items-center"
                            >
                              <ExternalLink className="h-4 w-4" />
                            </a>
                          ) : (
                            '-'
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        #
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Title
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Agency
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Reason Not Processed
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {paginatedUnprocessedOpportunities.map((opp, index) => (
                      <tr key={index}>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          {startIndex + index + 1}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          <div className="max-w-xs truncate" title={opp.title}>
                            {opp.title}
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                          {opp.agency}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">
                          <div className="flex items-center">
                            <AlertCircle className="h-4 w-4 mr-2 text-yellow-500" />
                            {opp.reason}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            
            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="mt-4 flex items-center justify-between px-4 py-3 bg-gray-50 border-t">
                <div className="flex-1 flex justify-between sm:hidden">
                  <button
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className={`relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md ${
                      currentPage === 1
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'bg-white text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className={`ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md ${
                      currentPage === totalPages
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'bg-white text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    Next
                  </button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      Showing{' '}
                      <span className="font-medium">{startIndex + 1}</span> to{' '}
                      <span className="font-medium">
                        {Math.min(
                          endIndex,
                          activeTab === 'processed' ? opportunities.length : unprocessedOpportunities.length
                        )}
                      </span>{' '}
                      of{' '}
                      <span className="font-medium">
                        {activeTab === 'processed' ? opportunities.length : unprocessedOpportunities.length}
                      </span>{' '}
                      results
                    </p>
                  </div>
                  <div>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                      <button
                        onClick={() => handlePageChange(currentPage - 1)}
                        disabled={currentPage === 1}
                        className={`relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 text-sm font-medium ${
                          currentPage === 1
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : 'bg-white text-gray-500 hover:bg-gray-50'
                        }`}
                      >
                        <span className="sr-only">Previous</span>
                        <ChevronLeft className="h-5 w-5" />
                      </button>
                      
                      {/* Page numbers */}
                      {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                        let pageNum: number;
                        if (totalPages <= 5) {
                          pageNum = i + 1;
                        } else if (currentPage <= 3) {
                          pageNum = i + 1;
                        } else if (currentPage >= totalPages - 2) {
                          pageNum = totalPages - 4 + i;
                        } else {
                          pageNum = currentPage - 2 + i;
                        }
                        
                        return (
                          <button
                            key={pageNum}
                            onClick={() => handlePageChange(pageNum)}
                            className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                              pageNum === currentPage
                                ? 'z-10 bg-indigo-50 border-indigo-500 text-indigo-600'
                                : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                            }`}
                          >
                            {pageNum}
                          </button>
                        );
                      })}
                      
                      <button
                        onClick={() => handlePageChange(currentPage + 1)}
                        disabled={currentPage === totalPages}
                        className={`relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 text-sm font-medium ${
                          currentPage === totalPages
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : 'bg-white text-gray-500 hover:bg-gray-50'
                        }`}
                      >
                        <span className="sr-only">Next</span>
                        <ChevronRight className="h-5 w-5" />
                      </button>
                    </nav>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DataIngestion;