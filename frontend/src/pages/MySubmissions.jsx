import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { submissionsAPI } from '../services/api';
import { ArrowLeft, AlertCircle, Loader, Code2 } from 'lucide-react';
import './MySubmissions.css';

const MySubmissions = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    fetchSubmissions();
  }, [user, navigate]);

  const fetchSubmissions = async () => {
    try {
      setLoading(true);
      const response = await submissionsAPI.getMy();
      const submissionsData = response.data || response;
      setSubmissions(Array.isArray(submissionsData) ? submissionsData : []);
    } catch (err) {
      console.error('Error fetching submissions:', err);
      setError(err.response?.data?.detail || 'Failed to load submissions');
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="my-submissions-container">
      <div className="my-submissions-header">
        <button className="btn-back" onClick={() => navigate('/dashboard')}>
          <ArrowLeft size={20} />
          Back to Dashboard
        </button>
        <h1>My Submissions</h1>
      </div>

      {error && (
        <div className="error-message">
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading">
          <Loader className="spinner" size={32} />
          Loading submissions...
        </div>
      ) : submissions.length === 0 ? (
        <div className="empty-state">
          <Code2 size={48} />
          <p>No submissions yet</p>
          <button 
            className="btn-primary"
            onClick={() => navigate('/challenges')}
          >
            Browse Challenges
          </button>
        </div>
      ) : (
        <div className="submissions-grid">
          {submissions.map((submission) => (
            <div 
              key={submission.id} 
              className="submission-card"
              onClick={() => submission.challenge_id && navigate(`/challenges/${submission.challenge_id}`)}
            >
              <div className="submission-card-header">
                {submission.challenge_title && (
                  <h3 className="challenge-title">{submission.challenge_title}</h3>
                )}
                <div className="badges">
                  <span className={`status-badge ${submission.status?.toLowerCase()}`}>
                    {submission.status}
                  </span>
                  <span className="language-badge">{submission.language}</span>
                </div>
              </div>
              <div className="submission-card-body">
                <div className="score-section">
                  <span className="score-label">Score</span>
                  <span className="score-value">{submission.score}%</span>
                </div>
                <div className="submission-meta">
                  <p className="submission-time">
                    {new Date(submission.created_at).toLocaleString()}
                  </p>
                  {submission.time_ms_total > 0 && (
                    <p className="submission-time-ms">
                      Time: {submission.time_ms_total}ms
                    </p>
                  )}
                  {submission.cases && submission.cases.length > 0 && (
                    <p className="test-cases-info">
                      {submission.cases.filter(c => c.status === 'ACCEPTED').length} / {submission.cases.length} test cases passed
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MySubmissions;

