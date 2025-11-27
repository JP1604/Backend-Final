import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { challengesAPI } from '../services/api';
import { ArrowLeft, AlertCircle, Loader, Code2, Plus, X, Settings } from 'lucide-react';
import './ChallengeDetail.css';

const ChallengeDetail = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { id } = useParams();
  const [challenge, setChallenge] = useState(null);
  const [testCases, setTestCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showTestCasesModal, setShowTestCasesModal] = useState(false);
  const [showAddTestCase, setShowAddTestCase] = useState(false);
  const [newTestCase, setNewTestCase] = useState({
    input: '',
    expected_output: '',
    is_hidden: false,
    order_index: 1
  });

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
      
      // Fetch test cases if user is professor or admin
      if (user?.role === 'PROFESSOR' || user?.role === 'ADMIN') {
        await fetchTestCases();
      }
    } catch (err) {
      console.error('Error fetching challenge:', err);
      setError(err.response?.data?.detail || 'Failed to load challenge');
    } finally {
      setLoading(false);
    }
  };

  const fetchTestCases = async () => {
    try {
      const response = await challengesAPI.getTestCases(id);
      const testCasesData = response.data || response;
      setTestCases(Array.isArray(testCasesData) ? testCasesData : []);
    } catch (err) {
      console.error('Error fetching test cases:', err);
      // Don't show error if test cases can't be fetched, just log it
    }
  };

  const handleAddTestCase = async (e) => {
    e.preventDefault();
    try {
      setError('');
      const testCaseData = {
        input: newTestCase.input.trim(),
        expected_output: newTestCase.expected_output.trim(),
        is_hidden: newTestCase.is_hidden,
        order_index: parseInt(newTestCase.order_index) || testCases.length + 1
      };
      
      await challengesAPI.createTestCase(id, testCaseData);
      setShowAddTestCase(false);
      setNewTestCase({
        input: '',
        expected_output: '',
        is_hidden: false,
        order_index: testCases.length + 1
      });
      await fetchTestCases();
    } catch (err) {
      console.error('Error creating test case:', err);
      setError(err.response?.data?.detail || 'Failed to create test case');
    }
  };

  const isTeacher = user?.role === 'PROFESSOR' || user?.role === 'ADMIN';

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

          {isTeacher && (
            <div className="challenge-actions">
              <button 
                className="btn-manage-test-cases"
                onClick={() => {
                  setShowTestCasesModal(true);
                  fetchTestCases();
                }}
              >
                <Settings size={20} />
                Manage Test Cases ({testCases.length})
              </button>
            </div>
          )}

          {/* Test Cases Modal */}
          {showTestCasesModal && (
            <div className="modal-overlay" onClick={() => setShowTestCasesModal(false)}>
              <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                  <h3>Manage Test Cases</h3>
                  <button className="btn-close" onClick={() => setShowTestCasesModal(false)}>
                    <X size={20} />
                  </button>
                </div>
                
                <div className="test-cases-section">
                  <div className="test-cases-header">
                    <h4>Test Cases ({testCases.length})</h4>
                    <button 
                      className="btn-add-test-case"
                      onClick={() => setShowAddTestCase(true)}
                    >
                      <Plus size={18} />
                      Add Test Case
                    </button>
                  </div>

                  {testCases.length === 0 ? (
                    <p className="empty-text">No test cases yet. Add one to get started.</p>
                  ) : (
                    <div className="test-cases-list">
                      {testCases.map((tc, index) => (
                        <div key={tc.id} className="test-case-item">
                          <div className="test-case-header">
                            <span className="test-case-number">Test Case #{tc.order_index || index + 1}</span>
                            {tc.is_hidden && (
                              <span className="hidden-badge">Hidden</span>
                            )}
                          </div>
                          <div className="test-case-content">
                            <div className="test-case-field">
                              <label>Input:</label>
                              <pre className="test-case-value">{tc.input}</pre>
                            </div>
                            <div className="test-case-field">
                              <label>Expected Output:</label>
                              <pre className="test-case-value">{tc.expected_output}</pre>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Add Test Case Form */}
                {showAddTestCase && (
                  <div className="add-test-case-form">
                    <h4>Add New Test Case</h4>
                    <form onSubmit={handleAddTestCase}>
                      <div className="form-group">
                        <label>Input *</label>
                        <textarea
                          value={newTestCase.input}
                          onChange={(e) => setNewTestCase({ ...newTestCase, input: e.target.value })}
                          rows={4}
                          placeholder="Enter test input (e.g., '1\n2' or 'hello')"
                          required
                        />
                      </div>
                      <div className="form-group">
                        <label>Expected Output *</label>
                        <textarea
                          value={newTestCase.expected_output}
                          onChange={(e) => setNewTestCase({ ...newTestCase, expected_output: e.target.value })}
                          rows={4}
                          placeholder="Enter expected output (e.g., '3' or 'olleh')"
                          required
                        />
                      </div>
                      <div className="form-row">
                        <div className="form-group">
                          <label>Order Index</label>
                          <input
                            type="number"
                            value={newTestCase.order_index}
                            onChange={(e) => setNewTestCase({ ...newTestCase, order_index: parseInt(e.target.value) || 1 })}
                            min="1"
                          />
                        </div>
                        <div className="form-group">
                          <label>
                            <input
                              type="checkbox"
                              checked={newTestCase.is_hidden}
                              onChange={(e) => setNewTestCase({ ...newTestCase, is_hidden: e.target.checked })}
                            />
                            Hidden (students won't see this test case)
                          </label>
                        </div>
                      </div>
                      <div className="form-actions">
                        <button type="submit" className="btn-primary">Add Test Case</button>
                        <button 
                          type="button" 
                          className="btn-secondary" 
                          onClick={() => {
                            setShowAddTestCase(false);
                            setNewTestCase({
                              input: '',
                              expected_output: '',
                              is_hidden: false,
                              order_index: testCases.length + 1
                            });
                          }}
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  </div>
                )}
              </div>
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

