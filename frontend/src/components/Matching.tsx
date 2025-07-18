import React, { useState, useEffect } from 'react';
import { Search, TrendingUp, Calendar, ExternalLink, ChevronRight, AlertCircle, User, ChevronDown, ChevronUp, Lightbulb, FileText } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_BASE = 'http://localhost:5001/api';

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

interface ExistingUser {
  id: string;
  name: string;
}

interface Explanation {
  summary: string;
  alignment_reasons: string[];
  reusable_content: Array<{
    source: string;
    content: string;
    relevance: string;
  }>;
  next_steps: string[];
}

const Matching: React.FC = () => {
  const navigate = useNavigate();
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [numResults, setNumResults] = useState(20);
  const [users, setUsers] = useState<ExistingUser[]>([]);
  const [selectedUser, setSelectedUser] = useState<string>('');
  const [expandedMatch, setExpandedMatch] = useState<number | null>(null);
  const [explanations, setExplanations] = useState<{ [key: number]: Explanation }>({});
  const [loadingExplanation, setLoadingExplanation] = useState<number | null>(null);
  const [progress, setProgress] = useState<string>('');
  const [totalOpportunities, setTotalOpportunities] = useState<number>(0);

  useEffect(() => {
    fetchUsers();
    fetchTotalOpportunities();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API_BASE}/users`);
      if (response.data.success && response.data.users.length > 0) {
        setUsers(response.data.users);
        setSelectedUser(response.data.users[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch users:', error);
    }
  };

  const fetchTotalOpportunities = async () => {
    try {
      const response = await axios.get(`${API_BASE}/stats`);
      if (response.data.success && response.data.stats) {
        setTotalOpportunities(response.data.stats.opportunities || 0);
      }
    } catch (error) {
      console.error('Failed to fetch total opportunities:', error);
    }
  };

  const handleSearch = async () => {
    if (!selectedUser) {
      setError('Please select a user profile first');
      return;
    }

    setLoading(true);
    setError(null);
    setHasSearched(true);
    setExpandedMatch(null);
    setExplanations({});
    setProgress('Searching for matches using AI embeddings...');

    try {
      const response = await axios.post(`${API_BASE}/match`, {
        n_results: numResults === -1 ? 999999 : numResults,  // Send large number for "All"
        user_id: selectedUser,
      }, {
        timeout: 300000, // 5 minute timeout for large requests
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.data.success) {
        setMatches(response.data.matches);
      } else {
        setError(response.data.error || 'Failed to find matches');
      }
    } catch (error: any) {
      console.error('Matching error:', error);
      if (error.response) {
        // Server responded with error
        setError(error.response.data?.error || 'Server error occurred');
      } else if (error.request) {
        // Request made but no response
        setError('Failed to connect to server. Please ensure the backend is running.');
      } else {
        // Other error
        setError('An unexpected error occurred');
      }
    } finally {
      setLoading(false);
      setProgress('');
    }
  };

  const fetchExplanation = async (index: number) => {
    if (explanations[index]) return;
    
    setLoadingExplanation(index);
    try {
      const response = await axios.post(`${API_BASE}/opportunity/${index}/explain`, {
        opportunity: matches[index],
      });

      if (response.data.success) {
        setExplanations(prev => ({
          ...prev,
          [index]: response.data.explanation,
        }));
      }
    } catch (error) {
      console.error('Failed to fetch explanation:', error);
    } finally {
      setLoadingExplanation(null);
    }
  };

  const toggleExpand = async (index: number) => {
    if (expandedMatch === index) {
      setExpandedMatch(null);
    } else {
      setExpandedMatch(index);
      await fetchExplanation(index);
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
    sessionStorage.setItem('selectedMatch', JSON.stringify(matches[index]));
    navigate(`/opportunity/${index}`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Funding Opportunity Matching</h2>
        <p className="mt-2 text-gray-600">
          Select a user profile to find matching funding opportunities based on their research expertise.
        </p>
      </div>

      {/* Search Controls */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select User Profile
            </label>
            <div className="relative">
              <User className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
              <select
                value={selectedUser}
                onChange={(e) => setSelectedUser(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Select a user profile...</option>
                {users.map(user => (
                  <option key={user.id} value={user.id}>
                    {user.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

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
              {totalOpportunities > 100 && (
                <>
                  <option value={200}>200 Results</option>
                </>
              )}
              <option value={-1}>All ({totalOpportunities})</option>
            </select>
          </div>
          
          <button
            onClick={handleSearch}
            disabled={loading || !selectedUser}
            className={`w-full flex items-center justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
              loading || !selectedUser
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-700'
            }`}
          >
            <Search className="h-5 w-5 mr-2" />
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                {progress || 'Searching...'}
              </>
            ) : (
              'Find Matching Opportunities'
            )}
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

      {/* Loading State */}
      {loading && (
        <div className="bg-blue-50 rounded-lg p-6 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-blue-800 font-medium">{progress}</p>
          <p className="text-blue-600 text-sm mt-2">This may take a moment as we analyze opportunities...</p>
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
                Try creating or updating the user's profile with more information.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {matches.map((match, index) => (
                <div
                  key={index}
                  className="bg-white rounded-lg shadow hover:shadow-md transition-shadow"
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

                    {match.keywords && Array.isArray(match.keywords) && match.keywords.length > 0 && (
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
                      <div className="flex items-center space-x-4">
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
                        <button
                          onClick={() => toggleExpand(index)}
                          className="flex items-center text-sm text-indigo-600 hover:text-indigo-800"
                        >
                          <Lightbulb className="h-4 w-4 mr-1" />
                          {expandedMatch === index ? 'Hide' : 'Show'} AI Explanation
                          {expandedMatch === index ? (
                            <ChevronUp className="h-4 w-4 ml-1" />
                          ) : (
                            <ChevronDown className="h-4 w-4 ml-1" />
                          )}
                        </button>
                      </div>
                      <button 
                        onClick={() => viewDetails(index)}
                        className="flex items-center text-sm text-gray-600 hover:text-gray-900"
                      >
                        View Details
                        <ChevronRight className="h-4 w-4 ml-1" />
                      </button>
                    </div>

                    {/* Inline Explanation */}
                    {expandedMatch === index && (
                      <div className="mt-4 pt-4 border-t border-gray-200">
                        {loadingExplanation === index ? (
                          <div className="text-center py-4">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
                            <p className="text-sm text-gray-600 mt-2">Generating AI explanation...</p>
                          </div>
                        ) : explanations[index] ? (
                          <div className="space-y-4">
                            <div>
                              <h5 className="font-medium text-gray-900 mb-2">Why This is a Match:</h5>
                              <p className="text-sm text-gray-700">{explanations[index].summary}</p>
                            </div>

                            {explanations[index].alignment_reasons && explanations[index].alignment_reasons.length > 0 && (
                              <div>
                                <h5 className="font-medium text-gray-900 mb-2">Key Alignment Points:</h5>
                                <ul className="list-disc list-inside space-y-1">
                                  {explanations[index].alignment_reasons.map((reason, idx) => (
                                    <li key={idx} className="text-sm text-gray-700">{reason}</li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {explanations[index].reusable_content && explanations[index].reusable_content.length > 0 && (
                              <div>
                                <h5 className="font-medium text-gray-900 mb-2">
                                  <FileText className="inline h-4 w-4 mr-1" />
                                  Reusable Content from Your Portfolio:
                                </h5>
                                <div className="space-y-2">
                                  {explanations[index].reusable_content.map((content, idx) => (
                                    <div key={idx} className="bg-gray-50 rounded p-3">
                                      <p className="text-sm font-medium text-gray-700">{content.source}</p>
                                      <p className="text-sm text-gray-600 mt-1">{content.content}</p>
                                      <p className="text-xs text-gray-500 mt-1">Relevance: {content.relevance}</p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {explanations[index].next_steps && explanations[index].next_steps.length > 0 && (
                              <div>
                                <h5 className="font-medium text-gray-900 mb-2">Recommended Next Steps:</h5>
                                <ol className="list-decimal list-inside space-y-2">
                                  {explanations[index].next_steps.map((step, idx) => {
                                    // Parse step to check if it has a title (text before colon)
                                    const colonIndex = step.indexOf(':');
                                    if (colonIndex > 0 && colonIndex < 50) {
                                      const title = step.substring(0, colonIndex).trim();
                                      const content = step.substring(colonIndex + 1).trim();
                                      return (
                                        <li key={idx} className="text-sm text-gray-700">
                                          <span className="font-semibold">{title}:</span> {content}
                                        </li>
                                      );
                                    }
                                    return (
                                      <li key={idx} className="text-sm text-gray-700">{step}</li>
                                    );
                                  })}
                                </ol>
                              </div>
                            )}
                          </div>
                        ) : (
                          <p className="text-sm text-gray-600">Failed to load explanation.</p>
                        )}
                      </div>
                    )}
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
            <li>• Select a user profile from the dropdown to search for relevant opportunities</li>
            <li>• The system uses AI embeddings to find semantic matches</li>
            <li>• Confidence scores indicate how well opportunities match the user's profile</li>
            <li>• Click "Show AI Explanation" to see detailed matching reasons</li>
            <li>• The AI will suggest reusable content from the user's portfolio</li>
            <li>• Higher scores (≥70%) indicate strong alignment with expertise</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default Matching;