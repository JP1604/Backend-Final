import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { examsAPI, challengesAPI, submissionsAPI } from '../services/api';
import { ArrowLeft, AlertCircle, Loader, CheckCircle, XCircle, Clock, Send, FileText } from 'lucide-react';
import './ExamAttempt.css';

const ExamAttempt = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { examId, attemptId } = useParams();
  const [exam, setExam] = useState(null);
  const [challenges, setChallenges] = useState([]);
  const [selectedChallenge, setSelectedChallenge] = useState(null);
  const [code, setCode] = useState('');
  const [submissions, setSubmissions] = useState({}); // challenge_id -> latest submission
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [timeRemaining, setTimeRemaining] = useState(null);
  const [attemptStartedAt, setAttemptStartedAt] = useState(null);

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    if (user.role !== 'STUDENT') {
      setError('Only students can take exams');
      return;
    }

    fetchExamData();
  }, [user, navigate, examId, attemptId]);

  useEffect(() => {
    if (attemptStartedAt && exam) {
      const interval = setInterval(() => {
        const now = new Date();
        const started = new Date(attemptStartedAt);
        const elapsed = Math.floor((now - started) / 1000 / 60); // minutes
        const remaining = exam.duration_minutes - elapsed;
        setTimeRemaining(Math.max(0, remaining));
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [attemptStartedAt, exam]);

  const fetchExamData = async () => {
    try {
      setLoading(true);
      
      // Fetch exam details
      const examResp = await examsAPI.getById(examId);
      setExam(examResp.data || examResp);

      // Fetch exam challenges
      const challengesResp = await examsAPI.getChallenges(examId);
      const challengesData = Array.isArray(challengesResp.data) ? challengesResp.data : [];
      setChallenges(challengesData);

      // Fetch user's submissions for these challenges first
      await fetchSubmissions(challengesData.map(c => c.challenge_id));

      // Select first challenge by default
      if (challengesData.length > 0) {
        await loadChallenge(challengesData[0].challenge_id);
      }

      // Fetch attempt info to get started_at
      // We'll need to get this from the backend or store it when starting
      const now = new Date();
      setAttemptStartedAt(now.toISOString());
    } catch (err) {
      console.error('Error fetching exam data:', err);
      setError(err.response?.data?.detail || 'Failed to load exam');
    } finally {
      setLoading(false);
    }
  };

  const fetchSubmissions = async (challengeIds) => {
    try {
      const submissionsResp = await submissionsAPI.getMy();
      const allSubmissions = Array.isArray(submissionsResp.data) ? submissionsResp.data : [];
      
      const submissionsMap = {};
      challengeIds.forEach(challengeId => {
        const challengeSubs = allSubmissions
          .filter(s => s.challenge_id === challengeId)
          .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        if (challengeSubs.length > 0) {
          submissionsMap[challengeId] = challengeSubs[0];
        }
      });
      
      setSubmissions(submissionsMap);
    } catch (err) {
      console.error('Error fetching submissions:', err);
    }
  };

  const loadChallenge = async (challengeId) => {
    try {
      const challengeResp = await challengesAPI.getById(challengeId);
      const challengeData = challengeResp.data || challengeResp;
      setSelectedChallenge(challengeData);
      
      // Load latest submission code if exists
      const latestSubmission = submissions[challengeId];
      if (latestSubmission && latestSubmission.code) {
        setCode(latestSubmission.code);
      } else {
        setCode('');
      }
    } catch (err) {
      console.error('Error loading challenge:', err);
      setError(err.response?.data?.detail || 'Failed to load challenge');
    }
  };

  const handleChallengeSelect = (challengeId) => {
    loadChallenge(challengeId);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!code.trim()) {
      setError('Code cannot be empty');
      return;
    }

    if (!selectedChallenge) {
      setError('No challenge selected');
      return;
    }

    // Check if this challenge already has an accepted submission
    const existingSubmission = submissions[selectedChallenge.id];
    if (existingSubmission && existingSubmission.status === 'ACCEPTED') {
      setError('This challenge has already been completed. You cannot submit again.');
      return;
    }

    try {
      setSubmitting(true);
      const response = await submissionsAPI.submit(selectedChallenge.id, code, attemptId);
      
      setSuccess('Code submitted successfully! Processing...');
      
      // Wait a bit for processing
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Refresh submissions
      await fetchSubmissions([selectedChallenge.id]);
      
      // Poll for results
      let attempts = 0;
      const maxAttempts = 10;
      const pollInterval = setInterval(async () => {
        try {
          const submissionsResp = await submissionsAPI.getMy();
          const allSubmissions = Array.isArray(submissionsResp.data) ? submissionsResp.data : [];
          const challengeSubs = allSubmissions
            .filter(s => s.challenge_id === selectedChallenge.id)
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
          
          if (challengeSubs.length > 0) {
            const latest = challengeSubs[0];
            setSubmissions(prev => ({
              ...prev,
              [selectedChallenge.id]: latest
            }));
            
            if (latest.status !== 'QUEUED' && latest.status !== 'RUNNING') {
              clearInterval(pollInterval);
              setSuccess('Submission processed!');
              // If accepted, disable editing this challenge
              if (latest.status === 'ACCEPTED') {
                setCode(''); // Clear code to prevent further edits
              }
            }
          }
        } catch (err) {
          console.error('Error polling submissions:', err);
        }
        
        attempts++;
        if (attempts >= maxAttempts) {
          clearInterval(pollInterval);
        }
      }, 2000);
    } catch (err) {
      console.error('Error submitting code:', err);
      setError(err.response?.data?.detail || 'Failed to submit code');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmitExam = async () => {
    if (!window.confirm('Are you sure you want to submit the exam? You will not be able to make any more changes.')) {
      return;
    }

    try {
      setSubmitting(true);
      setError('');
      const response = await examsAPI.submitAttempt(attemptId);
      setSuccess(`Exam submitted successfully! Score: ${response.data?.score || 0}%`);
      
      // Redirect to exams page after a short delay
      setTimeout(() => {
        navigate('/exams');
      }, 1500);
    } catch (err) {
      console.error('Error submitting exam:', err);
      setError(err.response?.data?.detail || 'Failed to submit exam');
      setSubmitting(false);
    }
  };

  const getSubmissionStatus = (challengeId) => {
    const submission = submissions[challengeId];
    if (!submission) return null;
    
    if (submission.status === 'ACCEPTED') {
      return { icon: CheckCircle, color: 'green', text: 'Accepted' };
    } else if (submission.status === 'WRONG_ANSWER' || submission.status === 'RUNTIME_ERROR' || submission.status === 'TIME_LIMIT_EXCEEDED') {
      return { icon: XCircle, color: 'red', text: submission.status.replace('_', ' ') };
    } else if (submission.status === 'QUEUED' || submission.status === 'RUNNING') {
      return { icon: Loader, color: 'orange', text: 'Processing...' };
    }
    return { icon: AlertCircle, color: 'gray', text: submission.status };
  };

  if (!user || user.role !== 'STUDENT') return null;

  if (loading && !exam) {
    return (
      <div className="exam-attempt-container">
        <div className="loading">
          <Loader className="spinner" size={32} />
          Loading exam...
        </div>
      </div>
    );
  }

  if (error && !exam) {
    return (
      <div className="exam-attempt-container">
        <button className="btn-back" onClick={() => navigate('/exams')}>
          <ArrowLeft size={20} /> Back to Exams
        </button>
        <div className="error-message">
          <AlertCircle size={20} />
          {error}
        </div>
      </div>
    );
  }

  const formatTime = (minutes) => {
    const hrs = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hrs > 0 ? `${hrs}h ${mins}m` : `${mins}m`;
  };

  return (
    <div className="exam-attempt-container">
      <div className="exam-attempt-header">
        <button className="btn-back" onClick={() => navigate('/exams')}>
          <ArrowLeft size={20} /> Back to Exams
        </button>
        <div className="exam-header-info">
          <h1>{exam?.title || 'Exam'}</h1>
          {timeRemaining !== null && (
            <div className="time-remaining">
              <Clock size={20} />
              <span>Time Remaining: {formatTime(timeRemaining)}</span>
            </div>
          )}
        </div>
      </div>

      {exam && (
        <div className="exam-info">
          <p>{exam.description}</p>
          <div className="exam-constraints">
            <span>Duration: {exam.duration_minutes} minutes</span>
            <span>Max Attempts: {exam.max_attempts}</span>
            {exam.passing_score && <span>Passing Score: {exam.passing_score}%</span>}
          </div>
        </div>
      )}

      <div className="exam-attempt-layout">
        {/* Challenges Sidebar */}
        <div className="challenges-sidebar">
          <h2>Challenges</h2>
          <div className="challenges-list">
            {challenges.map((challenge, index) => {
              const status = getSubmissionStatus(challenge.challenge_id);
              return (
                <div
                  key={challenge.challenge_id}
                  className={`challenge-item ${selectedChallenge?.id === challenge.challenge_id ? 'active' : ''}`}
                  onClick={() => {
                    // Don't allow selecting a challenge that's already been accepted
                    const status = getSubmissionStatus(challenge.challenge_id);
                    if (status && status.text === 'Accepted') {
                      return; // Don't allow selection
                    }
                    handleChallengeSelect(challenge.challenge_id);
                  }}
                  style={{ 
                    opacity: (getSubmissionStatus(challenge.challenge_id)?.text === 'Accepted') ? 0.6 : 1,
                    cursor: (getSubmissionStatus(challenge.challenge_id)?.text === 'Accepted') ? 'not-allowed' : 'pointer'
                  }}
                >
                  <div className="challenge-item-header">
                    <FileText size={18} />
                    <span>Challenge {index + 1}</span>
                    <span className="points">{challenge.points} pts</span>
                  </div>
                  <div className="challenge-item-title">{challenge.title}</div>
                  {status && (
                    <div className="challenge-status" style={{ color: status.color }}>
                      {status.icon && <status.icon size={14} />}
                      <span>{status.text}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          <button
            className="btn-submit-exam"
            onClick={handleSubmitExam}
            disabled={submitting}
          >
            Submit Exam
          </button>
        </div>

        {/* Challenge Content */}
        <div className="challenge-content">
          {selectedChallenge ? (
            <>
              <div className="challenge-header">
                <h2>{selectedChallenge.title}</h2>
                <div className="challenge-meta">
                  <span>Points: {challenges.find(c => c.challenge_id === selectedChallenge.id)?.points || 0}</span>
                  <span>Language: {selectedChallenge.language?.toUpperCase() || 'N/A'}</span>
                </div>
              </div>

              <div className="challenge-description">
                <p>{selectedChallenge.description}</p>
                <div className="challenge-constraints">
                  <span>Time Limit: {selectedChallenge.time_limit}ms</span>
                  <span>Memory Limit: {selectedChallenge.memory_limit}MB</span>
                </div>
              </div>

              <form onSubmit={handleSubmit} className="submission-form">
                <div className="form-group">
                  <label>Your Solution</label>
                  <textarea
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    className="code-textarea"
                    placeholder="Paste your code here..."
                    disabled={submitting || (submissions[selectedChallenge.id]?.status === 'ACCEPTED')}
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
                  disabled={submitting || (submissions[selectedChallenge.id]?.status === 'ACCEPTED')}
                >
                  {submitting ? (
                    <>
                      <Loader size={20} className="spinner-sm" />
                      Submitting...
                    </>
                  ) : (
                    <>
                      <Send size={20} />
                      Submit Solution
                    </>
                  )}
                </button>
              </form>

              {/* Latest Submission Status */}
              {submissions[selectedChallenge.id] && (
                <div className="submission-status">
                  <h3>Latest Submission</h3>
                  <div className="submission-details">
                    <p>Status: <strong>{submissions[selectedChallenge.id].status}</strong></p>
                    {submissions[selectedChallenge.id].score !== null && (
                      <p>Score: <strong>{submissions[selectedChallenge.id].score}%</strong></p>
                    )}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="no-challenge-selected">
              <p>Select a challenge from the sidebar to begin</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ExamAttempt;

