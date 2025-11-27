import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { challengesAPI } from '../services/api';
import { ArrowLeft, AlertCircle, Loader } from 'lucide-react';
import './Challenges.css';

const Challenges = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { id } = useParams();
  const [challenges, setChallenges] = useState([]);
  const [selectedChallenge, setSelectedChallenge] = useState(null);
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
        
        // Si hay un id en la URL, seleccionar ese challenge
        if (id) {
          const selected = (Array.isArray(data) ? data : []).find(c => c.id === id);
          setSelectedChallenge(selected);
        }
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
  }, [user, navigate, id]);

  if (!user) return null;

  const handleSelectChallenge = (challenge) => {
    setSelectedChallenge(challenge);
    navigate(`/challenges/${challenge.id}`);
  };

  const handleSolve = (challenge) => {
    navigate(`/solve/${challenge.id}`);
  };

  return (
    <div className="challenges-container">
      <div className="challenges-layout">
        {/* List */}
        <div className="challenges-list">
          <h2>Challenges</h2>
          {loading ? (
            <div className="loading">
              <Loader className="spinner" size={32} />
              Loading challenges...
            </div>
          ) : error ? (
            <div className="error-message">
              <AlertCircle size={20} />
              {error}
            </div>
          ) : challenges.length === 0 ? (
            <div className="empty-state">
              No challenges available yet
            </div>
          ) : (
            <div className="challenges-items">
              {challenges.map((challenge) => (
                <div
                  key={challenge.id}
                  className={`challenge-item ${selectedChallenge?.id === challenge.id ? 'active' : ''}`}
                  onClick={() => handleSelectChallenge(challenge)}
                >
                  <div className="challenge-item-header">
                    <h3>{challenge.title}</h3>
                    <span className={`difficulty-badge ${challenge.difficulty?.toLowerCase()}`}>
                      {challenge.difficulty}
                    </span>
                  </div>
                  <p className="challenge-item-desc">
                    {challenge.description?.substring(0, 100)}...
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Detail */}
        <div className="challenges-detail">
          {selectedChallenge ? (
            <div className="challenge-detail-content">
              <button 
                className="btn-back"
                onClick={() => setSelectedChallenge(null)}
              >
                <ArrowLeft size={20} /> Back
              </button>

              <h1>{selectedChallenge.title}</h1>
              <div className="challenge-meta">
                <span className={`difficulty-badge ${selectedChallenge.difficulty?.toLowerCase()}`}>
                  {selectedChallenge.difficulty}
                </span>
              </div>

              <div className="challenge-section">
                <h3>Description</h3>
                <p>{selectedChallenge.description}</p>
              </div>

              <div className="challenge-section">
                <h3>Constraints</h3>
                <ul>
                  <li>Time Limit: {selectedChallenge.time_limit}ms</li>
                  <li>Memory Limit: {selectedChallenge.memory_limit}MB</li>
                </ul>
              </div>

              <button 
                className="btn-submit"
                onClick={() => handleSolve(selectedChallenge)}
              >
                Solve Challenge
              </button>
            </div>
          ) : (
            <div className="challenges-empty">
              <p>Select a challenge to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Challenges;
