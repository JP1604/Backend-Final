import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { submissionsAPI, challengesAPI } from '../services/api';
import { Send, ArrowLeft, AlertCircle, CheckCircle, Loader } from 'lucide-react';
import './Submissions.css';

const Submissions = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { challengeId } = useParams();
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [challenge, setChallenge] = useState(null);
  const [mySubmissions, setMySubmissions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    // Only students can submit solutions
    if (user.role !== 'STUDENT') {
      setError('Only students can submit solutions to challenges');
      return;
    }

    // Must have a challengeId to submit
    if (!challengeId) {
      navigate('/submissions');
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch challenge details
        const challengeResp = await challengesAPI.getById(challengeId);
        setChallenge(challengeResp.data || challengeResp);

        // Fetch user submissions for this specific challenge
        const submissionsResp = await submissionsAPI.getMy();
        const allSubmissions = Array.isArray(submissionsResp.data) ? submissionsResp.data : [];
        // Filter submissions for this challenge only
        setMySubmissions(allSubmissions.filter(s => s.challenge_id === challengeId));
      } catch (err) {
        console.error('Error fetching data:', err);
        setError(err.response?.data?.detail || 'Failed to load challenge');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user, navigate, challengeId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!code.trim()) {
      setError('Code cannot be empty');
      return;
    }

    if (!challengeId) {
      setError('No challenge selected');
      return;
    }

    try {
      setSubmitting(true);
      const response = await submissionsAPI.submit(challengeId, code, language);
      const data = response.data || response;
      
      setSuccess('Code submitted successfully!');
      setCode('');
      
      // Refresh submissions list for this challenge
      const submissionsResp = await submissionsAPI.getMy();
      const allSubmissions = Array.isArray(submissionsResp.data) ? submissionsResp.data : [];
      setMySubmissions(allSubmissions.filter(s => s.challenge_id === challengeId));
    } catch (err) {
      console.error('Error submitting code:', err);
      setError(err.response?.data?.detail || 'Failed to submit code');
    } finally {
      setSubmitting(false);
    }
  };

  if (!user || !challengeId) return null;

  if (loading && !challenge) {
    return (
      <div className="submissions-container">
        <div className="loading">
          <Loader className="spinner" size={32} />
          Loading challenge...
        </div>
      </div>
    );
  }

  if (error && !challenge) {
    return (
      <div className="submissions-container">
        <button className="btn-back" onClick={() => navigate('/challenges')}>
          <ArrowLeft size={20} /> Back to Challenges
        </button>
        <div className="error-message">
          <AlertCircle size={20} />
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="submissions-container">
      <button className="btn-back" onClick={() => challenge?.course_id ? navigate(`/courses/${challenge.course_id}`) : navigate('/challenges')}>
        <ArrowLeft size={20} /> {challenge?.course_id ? 'Back to Course' : 'Back to Challenges'}
      </button>

      <div className="submissions-content">
        <h1>{challenge ? `Solving: ${challenge.title}` : 'Submit Solution'}</h1>

        {challenge && (
          <div className="challenge-info">
            <p className="challenge-description">{challenge.description}</p>
            <div className="challenge-constraints">
              <span>Time Limit: {challenge.time_limit}ms</span>
              <span>Memory Limit: {challenge.memory_limit}MB</span>
            </div>
          </div>
        )}

        <div className="submissions-layout">
          {/* Code Editor */}
          <div className="code-editor-section">
            <h2>Submit Your Solution</h2>
            <form onSubmit={handleSubmit} className="submission-form">
              <div className="form-group">
                <label htmlFor="language">Language</label>
                <select
                  id="language"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="form-input"
                  disabled={submitting}
                >
                  <option value="python">Python</option>
                  <option value="javascript">JavaScript</option>
                  <option value="java">Java</option>
                  <option value="cpp">C++</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="code">Code</label>
                <textarea
                  id="code"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="code-textarea"
                  placeholder="Paste your code here..."
                  disabled={submitting}
                  rows={20}
                />
              </div>

              {error && (
                <div className="alert alert-error">
                  <AlertCircle size={20} />
                  {error}
                </div>
              )}

              {success && (
                <div className="alert alert-success">
                  <CheckCircle size={20} />
                  {success}
                </div>
              )}

              <button 
                type="submit" 
                className="btn-submit"
                disabled={submitting}
              >
                {submitting ? (
                  <>
                    <Loader size={20} className="spinner-sm" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <Send size={20} />
                    Submit Code
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Previous Submissions for this challenge */}
          <div className="submissions-history">
            <h2>My Submissions</h2>
            {mySubmissions.length === 0 ? (
              <p className="empty-text">No submissions for this challenge yet</p>
            ) : (
              <div className="submissions-list">
                {mySubmissions.map((submission) => (
                  <div 
                    key={submission.id} 
                    className="submission-item"
                  >
                    <div className="submission-header">
                      <div>
                        <span className={`status-badge ${submission.status?.toLowerCase()}`}>
                          {submission.status}
                        </span>
                        <span className="language-badge">{submission.language}</span>
                      </div>
                    </div>
                    <div className="submission-details">
                      <p>Score: <strong>{submission.score}%</strong></p>
                      <p className="submission-time">
                        {new Date(submission.created_at).toLocaleString()}
                      </p>
                      {submission.time_ms_total > 0 && (
                        <p className="submission-time-ms">
                          Time: {submission.time_ms_total}ms
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Submissions;
