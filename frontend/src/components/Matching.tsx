import React, { useState } from 'react';
import { Search, TrendingUp, Calendar, ExternalLink, ChevronRight, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

interface Match {
  title: string;
  agency: string;
  description: string;
  keywords: string[];
  deadline: string;
  url: string;
  confidence_score: number;
  similarity_score: number;
}

const Matching: React.FC = () => {
  const navigate = useNavigate();
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [numResults, setNumResults] = useState(20);

  const handleSearch = async () => {
    setLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const response = await axios.post(`${API_BASE}/match`, {
        n_results: numResults,
      });

      if (response.data.success) {
        setMatches(response.data.matches);
      } else {
        setError(response.data.error || 'Failed to find matches');
      }
    } catch (error) {
      setError('Failed to connect to server. Please ensure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 70) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 40) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getConfidenceLabel = (score: number) => {
    if (score >= 70) return 'High Match';
    if (score >= 40) return 'Medium Match';
    return 'Low Match';
  };

  const viewDetails = (index: number) => {
    // Store the match data in session storage for the detail view
    sessionStorage.setItem('selectedMatch', JSON.stringify(matches[index]));
    navigate(`/opportunity/${index}`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Funding Opportunity Matching</h2>
        <p className="mt-2 text-gray-600">
          Find funding opportunities that match your research profile and expertise.
        </p>
      </div>

      {/* Search Controls */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Number of Results
            </label>
            <select
              value={numResults}
              onChange={(e) => setNumResults(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value={10}>10 Results</option>
              <option value={20}>20 Results</option>
              <option value={50}>50 Results</option>
              <option value={100}>100 Results</option>
            </select>
          </div>
          
          <button
            onClick={handleSearch}
            disabled={loading}
            className={`w-full flex items-center justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-700'
            }`}
          >
            <Search className="h-5 w-5 mr-2" />
            {loading ? 'Searching...' : 'Find Matching Opportunities'}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 rounded-lg p-4 flex items-start">
          <AlertCircle className="h-5 w-5 text-red-600 mr-2 flex-shrink-0" />
          <span className="text-sm text-red-800">{error}</span>
        </div>
      )}

      {/* Results */}
      {hasSearched && !loading && !error && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">
              Found {matches.length} Matching Opportunities
            </h3>
            {matches.length > 0 && (
              <div className="text-sm text-gray-600">
                Sorted by relevance score
              </div>
            )}
          </div>

          {matches.length === 0 ? (
            <div className="bg-gray-50 rounded-lg p-8 text-center">
              <p className="text-gray-600">No matching opportunities found.</p>
              <p className="text-sm text-gray-500 mt-2">
                Try creating or updating your profile with more information.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {matches.map((match, index) => (
                <div
                  key={index}
                  className="bg-white rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => viewDetails(index)}
                >
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-3">
                      <h4 className="text-lg font-semibold text-gray-900 flex-1 pr-4">
                        {match.title}
                      </h4>
                      <div
                        className={`px-3 py-1 rounded-full text-sm font-medium border ${getConfidenceColor(
                          match.confidence_score
                        )}`}
                      >
                        <div className="flex items-center space-x-1">
                          <TrendingUp className="h-4 w-4" />
                          <span>{match.confidence_score}%</span>
                        </div>
                        <div className="text-xs mt-0.5">
                          {getConfidenceLabel(match.confidence_score)}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-4 text-sm text-gray-600 mb-3">
                      <span className="font-medium">{match.agency}</span>
                      {match.deadline && (
                        <>
                          <span>•</span>
                          <div className="flex items-center">
                            <Calendar className="h-4 w-4 mr-1" />
                            <span>Deadline: {match.deadline}</span>
                          </div>
                        </>
                      )}
                    </div>

                    <p className="text-gray-700 text-sm mb-3 line-clamp-2">
                      {match.description}
                    </p>

                    {match.keywords && match.keywords.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-3">
                        {match.keywords.slice(0, 5).map((keyword, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-gray-100 text-gray-700 rounded-md text-xs"
                          >
                            {keyword}
                          </span>
                        ))}
                        {match.keywords.length > 5 && (
                          <span className="text-xs text-gray-500">
                            +{match.keywords.length - 5} more
                          </span>
                        )}
                      </div>
                    )}

                    <div className="flex items-center justify-between">
                      <a
                        href={match.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="flex items-center text-sm text-indigo-600 hover:text-indigo-800"
                      >
                        <ExternalLink className="h-4 w-4 mr-1" />
                        View Original
                      </a>
                      <button className="flex items-center text-sm text-gray-600 hover:text-gray-900">
                        View Details
                        <ChevronRight className="h-4 w-4 ml-1" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Instructions */}
      {!hasSearched && (
        <div className="bg-blue-50 rounded-lg p-6">
          <h4 className="text-sm font-semibold text-blue-900 mb-2">How Matching Works</h4>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• The system uses AI embeddings to find semantic matches</li>
            <li>• Confidence scores indicate how well opportunities match your profile</li>
            <li>• Higher scores (≥70%) indicate strong alignment with your expertise</li>
            <li>• Click on any opportunity to see detailed explanations</li>
            <li>• Make sure you have created a profile before searching</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default Matching;