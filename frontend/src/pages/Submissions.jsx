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
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch challenge details
        if (challengeId) {
          const challengeResp = await challengesAPI.getById(challengeId);
          setChallenge(challengeResp.data || challengeResp);
        }

        // Fetch user submissions
        const submissionsResp = await submissionsAPI.getMy();
        setSubmissions(Array.isArray(submissionsResp.data) ? submissionsResp.data : []);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Failed to load data');
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
      
      // Refresh submissions list
      const submissionsResp = await submissionsAPI.getMy();
      setSubmissions(Array.isArray(submissionsResp.data) ? submissionsResp.data : []);
    } catch (err) {
      console.error('Error submitting code:', err);
      setError(err.response?.data?.detail || 'Failed to submit code');
    } finally {
      setSubmitting(false);
    }
  };

  if (!user) return null;

  return (
    <div className="submissions-container">
      <button className="btn-back" onClick={() => navigate('/challenges')}>
        <ArrowLeft size={20} /> Back to Challenges
      </button>

      <div className="submissions-content">
        <h1>{challenge ? `Solving: ${challenge.title}` : 'Submit Solution'}</h1>

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

          {/* Previous Submissions */}
          <div className="submissions-history">
            <h2>Previous Submissions</h2>
            {submissions.length === 0 ? (
              <p className="empty-text">No submissions yet</p>
            ) : (
              <div className="submissions-list">
                {submissions.map((submission) => (
                  <div key={submission.id} className="submission-item">
                    <div className="submission-header">
                      <span className={`status-badge ${submission.status?.toLowerCase()}`}>
                        {submission.status}
                      </span>
                      <span className="language-badge">{submission.language}</span>
                    </div>
                    <div className="submission-details">
                      <p>Score: <strong>{submission.score}%</strong></p>
                      <p className="submission-time">
                        {new Date(submission.created_at).toLocaleDateString()}
                      </p>
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
