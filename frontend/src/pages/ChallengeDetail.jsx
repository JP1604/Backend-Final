import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { challengesAPI } from '../services/api';
import { ArrowLeft, AlertCircle, Loader, Code2 } from 'lucide-react';
import './ChallengeDetail.css';

const ChallengeDetail = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { id } = useParams();
  const [challenge, setChallenge] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    fetchChallenge();
  }, [user, navigate, id]);

  const fetchChallenge = async () => {
    try {
      setLoading(true);
      const response = await challengesAPI.getById(id);
      setChallenge(response.data || response);
    } catch (err) {
      console.error('Error fetching challenge:', err);
      setError(err.response?.data?.detail || 'Failed to load challenge');
    } finally {
      setLoading(false);
    }
  };

  const handleSolve = () => {
    // Only students can solve challenges
    if (user?.role !== 'STUDENT') {
      setError('Only students can solve challenges');
      return;
    }
    navigate(`/submissions/${id}`);
  };

  const canSolve = user?.role === 'STUDENT';

  if (!user) return null;

  return (
    <div className="challenge-detail-container">
      <button 
        className="btn-back"
        onClick={() => navigate('/challenges')}
      >
        <ArrowLeft size={20} />
        Back to Challenges
      </button>

      {loading ? (
        <div className="loading">
          <Loader className="spinner" size={32} />
          Loading challenge...
        </div>
      ) : error ? (
        <div className="error-message">
          <AlertCircle size={20} />
          {error}
        </div>
      ) : challenge ? (
        <div className="challenge-detail-content">
          <div className="challenge-header">
            <h1>{challenge.title}</h1>
            <span className={`difficulty-badge ${challenge.difficulty?.toLowerCase()}`}>
              {challenge.difficulty}
            </span>
          </div>

          <div className="challenge-section">
            <h3>Description</h3>
            <p>{challenge.description}</p>
          </div>

          <div className="challenge-section">
            <h3>Constraints</h3>
            <ul>
              <li>Time Limit: {challenge.time_limit}ms</li>
              <li>Memory Limit: {challenge.memory_limit}MB</li>
            </ul>
          </div>

          {challenge.tags && challenge.tags.length > 0 && (
            <div className="challenge-section">
              <h3>Tags</h3>
              <div className="tags-list">
                {challenge.tags.map((tag, index) => (
                  <span key={index} className="tag">{tag}</span>
                ))}
              </div>
            </div>
          )}

          {canSolve ? (
            <button 
              className="btn-submit"
              onClick={handleSolve}
            >
              <Code2 size={20} />
              Solve Challenge
            </button>
          ) : (
            <div className="info-message">
              <p>Only students can solve challenges. Professors and administrators can view challenges but cannot submit solutions.</p>
            </div>
          )}
        </div>
      ) : (
        <div className="empty-state">
          <p>Challenge not found</p>
        </div>
      )}
    </div>
  );
};

export default ChallengeDetail;

