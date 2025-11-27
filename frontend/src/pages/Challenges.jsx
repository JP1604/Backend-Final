import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { challengesAPI } from '../services/api';
import { AlertCircle, Loader, GraduationCap, Code2 } from 'lucide-react';
import './Challenges.css';

const Challenges = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [challenges, setChallenges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    const fetchChallenges = async () => {
      try {
        setLoading(true);
        const response = await challengesAPI.getAll();
        const data = response.data || response;
        setChallenges(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error('Error fetching challenges:', err);
        if (err.code === 'ERR_NETWORK' || err.message?.includes('CORS')) {
          setError('Error de conexión. Verifica que el backend esté ejecutándose y que CORS esté configurado correctamente.');
        } else if (err.response?.status === 401) {
          setError('No autorizado. Por favor, inicia sesión nuevamente.');
          navigate('/login');
        } else if (err.response?.status === 403) {
          setError('No tienes permisos para ver los challenges.');
        } else {
          setError(err.response?.data?.detail || err.message || 'Error al cargar los challenges');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchChallenges();
  }, [user, navigate]);

  if (!user) return null;

  const handleChallengeClick = (challenge) => {
    navigate(`/challenges/${challenge.id}`);
  };

  return (
    <div className="challenges-container">
      <div className="challenges-header">
        <h1>Challenges</h1>
        <p className="challenges-subtitle">Explore and solve programming challenges</p>
      </div>

      {loading ? (
        <div className="loading">
          <Loader className="spinner" size={32} />
          <span>Loading challenges...</span>
        </div>
      ) : error ? (
        <div className="error-message">
          <AlertCircle size={20} />
          {error}
        </div>
      ) : challenges.length === 0 ? (
        <div className="empty-state">
          <p>No challenges available yet</p>
        </div>
      ) : (
        <div className="challenges-grid">
          {challenges.map((challenge) => (
            <div
              key={challenge.id}
              className="challenge-card"
              onClick={() => handleChallengeClick(challenge)}
            >
              <div className="challenge-card-header">
                <h3>{challenge.title}</h3>
                <span className={`difficulty-badge ${challenge.difficulty?.toLowerCase()}`}>
                  {challenge.difficulty}
                </span>
              </div>
              
              <div className="challenge-meta-top">
                {challenge.course_name && (
                  <div className="challenge-course">
                    <GraduationCap size={16} />
                    <span>{challenge.course_name}</span>
                  </div>
                )}
                {challenge.language && (
                  <div className="challenge-language">
                    <Code2 size={16} />
                    <span>{challenge.language.toUpperCase()}</span>
                  </div>
                )}
              </div>

              <p className="challenge-card-description">
                {challenge.description?.substring(0, 150)}
                {challenge.description?.length > 150 ? '...' : ''}
              </p>

              <div className="challenge-card-footer">
                <div className="challenge-meta">
                  <span className="meta-item">⏱️ {challenge.time_limit}ms</span>
                  <span className="meta-item">💾 {challenge.memory_limit}MB</span>
                </div>
                {challenge.tags && challenge.tags.length > 0 && (
                  <div className="challenge-tags">
                    {challenge.tags.slice(0, 3).map((tag, idx) => (
                      <span key={idx} className="tag">{tag}</span>
                    ))}
                    {challenge.tags.length > 3 && (
                      <span className="tag-more">+{challenge.tags.length - 3}</span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Challenges;
