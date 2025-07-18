import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  ExternalLink,
  Calendar,
  TrendingUp,
  FileText,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Loader,
} from 'lucide-react';
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

interface Explanation {
  match_explanation: string;
  reusable_content: Array<{
    document: string;
    how_to_reuse: string;
  }>;
  next_steps: string[];
  raw_explanation?: string;
}

const OpportunityDetail: React.FC = () => {
  const { index } = useParams<{ index: string }>();
  const navigate = useNavigate();
  const [match, setMatch] = useState<Match | null>(null);
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Load the match data from session storage
    const storedMatch = sessionStorage.getItem('selectedMatch');
    if (storedMatch) {
      setMatch(JSON.parse(storedMatch));
    }
  }, []);

  const fetchExplanation = async () => {
    if (!match) return;

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE}/opportunity/${index}/explain`, {
        opportunity: match,
      });

      if (response.data.success) {
        setExplanation(response.data.explanation);
      } else {
        setError(response.data.error || 'Failed to generate explanation');
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

  if (!match) {
    return (
      <div className="space-y-6">
        <button
          onClick={() => navigate('/matching')}
          className="flex items-center text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="h-5 w-5 mr-2" />
          Back to Matches
        </button>
        <div className="bg-yellow-50 rounded-lg p-4">
          <p className="text-yellow-800">No opportunity data found. Please go back and select an opportunity.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Navigation */}
      <button
        onClick={() => navigate('/matching')}
        className="flex items-center text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="h-5 w-5 mr-2" />
        Back to Matches
      </button>

      {/* Opportunity Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start justify-between mb-4">
          <h1 className="text-2xl font-bold text-gray-900 flex-1 pr-4">{match.title}</h1>
          <div
            className={`px-4 py-2 rounded-full text-sm font-medium border ${getConfidenceColor(
              match.confidence_score
            )}`}
          >
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5" />
              <span className="text-lg">{match.confidence_score}%</span>
            </div>
            <div className="text-xs mt-0.5 text-center">{getConfidenceLabel(match.confidence_score)}</div>
          </div>
        </div>

        <div className="flex items-center space-x-6 text-gray-600 mb-4">
          <span className="font-medium text-lg">{match.agency}</span>
          {match.deadline && (
            <div className="flex items-center">
              <Calendar className="h-5 w-5 mr-2" />
              <span>Deadline: {match.deadline}</span>
            </div>
          )}
        </div>

        <p className="text-gray-700 mb-4">{match.description}</p>

        {match.keywords && match.keywords.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Keywords</h3>
            <div className="flex flex-wrap gap-2">
              {match.keywords.map((keyword, idx) => (
                <span key={idx} className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-md text-sm">
                  {keyword}
                </span>
              ))}
            </div>
          </div>
        )}

        <a
          href={match.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center text-indigo-600 hover:text-indigo-800"
        >
          <ExternalLink className="h-5 w-5 mr-2" />
          View Full Opportunity
        </a>
      </div>

      {/* AI Explanation Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">AI Match Analysis</h2>
          {!explanation && !loading && (
            <button
              onClick={fetchExplanation}
              className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
            >
              <RefreshCw className="h-5 w-5 mr-2" />
              Generate Explanation
            </button>
          )}
        </div>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader className="h-8 w-8 text-indigo-600 animate-spin" />
            <span className="ml-3 text-gray-600">Analyzing match and generating recommendations...</span>
          </div>
        )}

        {error && (
          <div className="bg-red-50 rounded-lg p-4 flex items-start">
            <AlertCircle className="h-5 w-5 text-red-600 mr-2 flex-shrink-0" />
            <span className="text-sm text-red-800">{error}</span>
          </div>
        )}

        {explanation && !loading && (
          <div className="space-y-6">
            {/* Match Explanation */}
            <div>
              <h3 className="font-semibold text-gray-900 mb-2 flex items-center">
                <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                Why This Matches Your Profile
              </h3>
              <p className="text-gray-700">{explanation.match_explanation}</p>
            </div>

            {/* Reusable Content */}
            {explanation.reusable_content && explanation.reusable_content.length > 0 && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-2 flex items-center">
                  <FileText className="h-5 w-5 text-blue-600 mr-2" />
                  Reusable Content from Your Documents
                </h3>
                <div className="space-y-3">
                  {explanation.reusable_content.map((content, idx) => (
                    <div key={idx} className="bg-blue-50 rounded-lg p-4">
                      <div className="font-medium text-blue-900 mb-1">{content.document}</div>
                      <p className="text-sm text-blue-800">{content.how_to_reuse}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Next Steps */}
            {explanation.next_steps && explanation.next_steps.length > 0 && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-2 flex items-center">
                  <RefreshCw className="h-5 w-5 text-purple-600 mr-2" />
                  Recommended Next Steps
                </h3>
                <ol className="space-y-2">
                  {explanation.next_steps.map((step, idx) => (
                    <li key={idx} className="flex items-start">
                      <span className="flex-shrink-0 w-7 h-7 bg-purple-100 text-purple-700 rounded-full flex items-center justify-center text-sm font-medium mr-3">
                        {idx + 1}
                      </span>
                      <span className="text-gray-700">{step}</span>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Tips */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-sm font-semibold text-gray-900 mb-2">Application Tips</h3>
        <ul className="text-sm text-gray-700 space-y-1">
          <li>• Review the full solicitation carefully before starting your proposal</li>
          <li>• Contact the program officer with any questions about eligibility or scope</li>
          <li>• Start early - most proposals require significant preparation time</li>
          <li>• Consider forming collaborations if the opportunity encourages team proposals</li>
          <li>• Use the AI recommendations as a starting point, but tailor to the specific requirements</li>
        </ul>
      </div>
    </div>
  );
};

export default OpportunityDetail;