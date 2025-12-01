import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { examsAPI } from '../services/api';
import { ArrowLeft, AlertCircle, Loader, CheckCircle, XCircle, FileText } from 'lucide-react';
import './ExamResults.css';

const ExamResults = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { examId } = useParams();
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    if (user.role === 'STUDENT') {
      navigate('/exams');
      return;
    }

    fetchResults();
  }, [user, navigate, examId]);

  const fetchResults = async () => {
    try {
      setLoading(true);
      const response = await examsAPI.getResults(examId);
      setResults(response.data || response);
    } catch (err) {
      console.error('Error fetching exam results:', err);
      setError(err.response?.data?.detail || 'Failed to load exam results');
    } finally {
      setLoading(false);
    }
  };

  if (!user || user.role === 'STUDENT') return null;

  return (
    <div className="exam-results-container">
      <button 
        className="btn-back"
        onClick={() => navigate('/exams')}
      >
        <ArrowLeft size={20} />
        Back to Exams
      </button>

      {error && (
        <div className="error-message">
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading">
          <Loader className="spinner" size={32} />
          Loading exam results...
        </div>
      ) : results ? (
        <div className="exam-results-content">
          <div className="results-header">
            <h1>{results.exam_title}</h1>
            <div className="results-stats">
              <div className="stat-card">
                <FileText size={24} />
                <div>
                  <span className="stat-value">{results.total_attempts}</span>
                  <span className="stat-label">Total Attempts</span>
                </div>
              </div>
              <div className="stat-card">
                <CheckCircle size={24} />
                <div>
                  <span className="stat-value">{results.passed_attempts}</span>
                  <span className="stat-label">Passed</span>
                </div>
              </div>
              <div className="stat-card">
                <div>
                  <span className="stat-value">{results.average_score}%</span>
                  <span className="stat-label">Average Score</span>
                </div>
              </div>
            </div>
          </div>

          <div className="attempts-section">
            <h2>Student Attempts</h2>
            {results.attempts && results.attempts.length === 0 ? (
              <p className="empty-message">No attempts yet</p>
            ) : (
              <div className="attempts-table">
                <table>
                  <thead>
                    <tr>
                      <th>Student</th>
                      <th>Score</th>
                      <th>Passed</th>
                      <th>Started At</th>
                      <th>Submitted At</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.attempts?.map((attempt) => (
                      <tr key={attempt.id}>
                        <td>
                          {attempt.user_name || attempt.user_email || attempt.user_id}
                          {attempt.user_email && attempt.user_name && (
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginTop: '0.25rem' }}>
                              {attempt.user_email}
                            </div>
                          )}
                        </td>
                        <td>
                          <span className={`score-badge ${attempt.score >= 70 ? 'pass' : 'fail'}`}>
                            {attempt.score}%
                          </span>
                        </td>
                        <td>
                          {attempt.passed ? (
                            <CheckCircle size={20} className="icon-pass" />
                          ) : (
                            <XCircle size={20} className="icon-fail" />
                          )}
                        </td>
                        <td>
                          {attempt.started_at 
                            ? new Date(attempt.started_at).toLocaleString()
                            : 'N/A'}
                        </td>
                        <td>
                          {attempt.submitted_at 
                            ? new Date(attempt.submitted_at).toLocaleString()
                            : 'Not submitted'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <FileText size={48} />
          <p>No results available</p>
        </div>
      )}
    </div>
  );
};

export default ExamResults;


