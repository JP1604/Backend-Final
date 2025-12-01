import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { examsAPI, coursesAPI, challengesAPI } from '../services/api';
import { FileText, Clock, CheckCircle, AlertCircle, Loader, Plus, X, Code2, Trash2, Edit2 } from 'lucide-react';
import './Exams.css';

const Exams = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { courseId } = useParams();
  const [exams, setExams] = useState([]);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedCourse, setSelectedCourse] = useState(courseId || '');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedExamId, setSelectedExamId] = useState(null);
  const [examChallenges, setExamChallenges] = useState([]);
  const [allChallenges, setAllChallenges] = useState([]);
  const [showChallengesModal, setShowChallengesModal] = useState(false);
  const [showAddChallenge, setShowAddChallenge] = useState(false);
  const [editingExam, setEditingExam] = useState(null);
  const [showEditForm, setShowEditForm] = useState(false);
  const [newChallengeAssignment, setNewChallengeAssignment] = useState({
    challenge_id: '',
    points: 100,
    order_index: 0,
  });
  const [newExam, setNewExam] = useState({
    course_id: courseId || '',
    title: '',
    description: '',
    start_time: '',
    end_time: '',
    duration_minutes: 60,
    max_attempts: 1,
    passing_score: null,
  });

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    if (user.role === 'PROFESSOR' || user.role === 'ADMIN') {
      fetchCourses();
    }
    fetchExams();
  }, [user, navigate, courseId]);

  const fetchCourses = async () => {
    try {
      const response = await coursesAPI.getAll();
      const data = Array.isArray(response.data) ? response.data : [];
      setCourses(data);
    } catch (err) {
      console.error('Error fetching courses:', err);
    }
  };

  const fetchExams = async () => {
    try {
      setLoading(true);
      const params = selectedCourse || courseId;
      const response = await examsAPI.getAll(params);
      const data = Array.isArray(response.data) ? response.data : [];
      setExams(data);
    } catch (err) {
      console.error('Error fetching exams:', err);
      setError(err.response?.data?.detail || 'Failed to load exams');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedCourse || courseId) {
      fetchExams();
    }
  }, [selectedCourse, courseId]);

  const handleCreateExam = async (e) => {
    e.preventDefault();
    try {
      await examsAPI.create(newExam);
      setShowCreateForm(false);
      setNewExam({
        course_id: courseId || '',
        title: '',
        description: '',
        start_time: '',
        end_time: '',
        duration_minutes: 60,
        max_attempts: 1,
        passing_score: null,
      });
      fetchExams();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create exam');
    }
  };

  const handleStartExam = async (examId) => {
    try {
      const response = await examsAPI.startAttempt(examId);
      navigate(`/exams/${examId}/attempt/${response.data.attempt_id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start exam');
    }
  };

  const handleEditExam = (exam) => {
    setEditingExam(exam);
    setShowEditForm(true);
  };

  const handleUpdateExam = async (e) => {
    e.preventDefault();
    try {
      await examsAPI.update(editingExam.id, {
        title: editingExam.title,
        description: editingExam.description,
        start_time: editingExam.start_time,
        end_time: editingExam.end_time,
        duration_minutes: editingExam.duration_minutes,
        max_attempts: editingExam.max_attempts,
        passing_score: editingExam.passing_score,
        status: editingExam.status,
      });
      setShowEditForm(false);
      setEditingExam(null);
      fetchExams();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update exam');
    }
  };

  const handleManageChallenges = async (examId) => {
    setSelectedExamId(examId);
    setShowChallengesModal(true);
    await fetchExamChallenges(examId);
    if (user.role === 'PROFESSOR' || user.role === 'ADMIN') {
      await fetchAllChallenges();
    }
  };

  const fetchExamChallenges = async (examId) => {
    try {
      const response = await examsAPI.getChallenges(examId);
      setExamChallenges(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      console.error('Error fetching exam challenges:', err);
      setError(err.response?.data?.detail || 'Failed to load exam challenges');
    }
  };

  const fetchAllChallenges = async () => {
    try {
      const response = await challengesAPI.getAll();
      setAllChallenges(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      console.error('Error fetching challenges:', err);
    }
  };

  const handleAssignChallenge = async (e) => {
    e.preventDefault();
    try {
      await examsAPI.assignChallenge(
        selectedExamId,
        newChallengeAssignment.challenge_id,
        newChallengeAssignment.points,
        newChallengeAssignment.order_index
      );
      setShowAddChallenge(false);
      setNewChallengeAssignment({ challenge_id: '', points: 100, order_index: 0 });
      await fetchExamChallenges(selectedExamId);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to assign challenge');
    }
  };

  const handleUnassignChallenge = async (challengeId) => {
    if (!window.confirm('Are you sure you want to remove this challenge from the exam?')) {
      return;
    }
    try {
      await examsAPI.unassignChallenge(selectedExamId, challengeId);
      await fetchExamChallenges(selectedExamId);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to unassign challenge');
    }
  };

  if (!user) return null;

  const canCreateExam = user.role === 'PROFESSOR' || user.role === 'ADMIN';

  return (
    <div className="exams-container">
      <div className="exams-header">
        <h1>Exams</h1>
        {canCreateExam && (
          <button 
            className="btn-primary"
            onClick={() => setShowCreateForm(!showCreateForm)}
          >
            <Plus size={20} />
            Create Exam
          </button>
        )}
      </div>

      {canCreateExam && courses.length > 0 && (
        <div className="filter-section">
          <label>Filter by Course:</label>
          <select
            value={selectedCourse}
            onChange={(e) => setSelectedCourse(e.target.value)}
            className="course-select"
          >
            <option value="">All Courses</option>
            {courses.map((course) => (
              <option key={course.id} value={course.id}>
                {course.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {showCreateForm && canCreateExam && (
        <div className="create-exam-form">
          <h2>Create New Exam</h2>
          <form onSubmit={handleCreateExam}>
            <div className="form-group">
              <label>Course *</label>
              <select
                value={newExam.course_id}
                onChange={(e) => setNewExam({ ...newExam, course_id: e.target.value })}
                required
              >
                <option value="">Select a course</option>
                {courses.map((course) => (
                  <option key={course.id} value={course.id}>
                    {course.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Exam Title *</label>
              <input
                type="text"
                value={newExam.title}
                onChange={(e) => setNewExam({ ...newExam, title: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={newExam.description}
                onChange={(e) => setNewExam({ ...newExam, description: e.target.value })}
                rows={3}
              />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Start Time *</label>
                <input
                  type="datetime-local"
                  value={newExam.start_time}
                  onChange={(e) => setNewExam({ ...newExam, start_time: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>End Time *</label>
                <input
                  type="datetime-local"
                  value={newExam.end_time}
                  onChange={(e) => setNewExam({ ...newExam, end_time: e.target.value })}
                  required
                />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Duration (minutes) *</label>
                <input
                  type="number"
                  min="1"
                  value={newExam.duration_minutes}
                  onChange={(e) => setNewExam({ ...newExam, duration_minutes: parseInt(e.target.value) })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Max Attempts</label>
                <input
                  type="number"
                  min="1"
                  value={newExam.max_attempts}
                  onChange={(e) => setNewExam({ ...newExam, max_attempts: parseInt(e.target.value) })}
                />
              </div>
            </div>
            <div className="form-group">
              <label>Passing Score (0-100, optional)</label>
              <input
                type="number"
                min="0"
                max="100"
                value={newExam.passing_score || ''}
                onChange={(e) => setNewExam({ ...newExam, passing_score: e.target.value ? parseInt(e.target.value) : null })}
              />
            </div>
            <div className="form-actions">
              <button type="submit" className="btn-primary">Create</button>
              <button 
                type="button" 
                className="btn-secondary"
                onClick={() => setShowCreateForm(false)}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {error && (
        <div className="error-message">
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading">
          <Loader className="spinner" size={32} />
          Loading exams...
        </div>
      ) : exams.length === 0 ? (
        <div className="empty-state">
          <FileText size={48} />
          <p>No exams available yet</p>
          {canCreateExam && (
            <button 
              className="btn-primary"
              onClick={() => setShowCreateForm(true)}
            >
              Create Your First Exam
            </button>
          )}
        </div>
      ) : (
        <div className="exams-grid">
          {exams.map((exam) => (
            <div key={exam.id} className="exam-card">
              <div className="exam-header">
                <h3>{exam.title}</h3>
                <span className={`status-badge ${exam.status?.toLowerCase()}`}>
                  {exam.status}
                </span>
              </div>
              <p className="exam-description">{exam.description || 'No description'}</p>
              <div className="exam-info">
                <div className="info-item">
                  <Clock size={16} />
                  <span>Duration: {exam.duration_minutes} minutes</span>
                </div>
                {exam.max_attempts && (
                  <div className="info-item">
                    <span>Max Attempts: {exam.max_attempts}</span>
                  </div>
                )}
                {exam.start_time && (
                  <div className="exam-dates">
                    <small>
                      {new Date(exam.start_time).toLocaleString()} - 
                      {exam.end_time ? new Date(exam.end_time).toLocaleString() : 'No end time'}
                    </small>
                  </div>
                )}
              </div>
              <div className="exam-actions">
                {user.role === 'STUDENT' && exam.is_active && (
                  <button 
                    className="btn-primary"
                    onClick={() => handleStartExam(exam.id)}
                  >
                    Start Exam
                  </button>
                )}
                {user.role === 'STUDENT' && (exam.status === 'active' || exam.status === 'ACTIVE') && exam.is_active === false && (
                  <div className="error-message" style={{ marginTop: '0.5rem', padding: '0.75rem', fontSize: '0.875rem' }}>
                    <AlertCircle size={16} />
                    <span>Exam is not currently active. Check the exam dates.</span>
                  </div>
                )}
                {(user.role === 'PROFESSOR' || user.role === 'ADMIN') && (
                  <>
                    <button 
                      className="btn-secondary"
                      onClick={() => handleEditExam(exam)}
                    >
                      <Edit2 size={16} />
                      Edit
                    </button>
                    <button 
                      className="btn-secondary"
                      onClick={() => handleManageChallenges(exam.id)}
                    >
                      Manage Challenges
                    </button>
                    <button 
                      className="btn-secondary"
                      onClick={() => navigate(`/exams/${exam.id}/results`)}
                    >
                      View Results
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal for managing exam challenges */}
      {showChallengesModal && (
        <div className="modal-overlay" onClick={() => setShowChallengesModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Manage Exam Challenges</h2>
              <button className="modal-close" onClick={() => setShowChallengesModal(false)}>
                <X size={24} />
              </button>
            </div>
            
            <div className="modal-body">
              {(user.role === 'PROFESSOR' || user.role === 'ADMIN') && (
                <div className="challenge-actions">
                  <button
                    className="btn-primary"
                    onClick={() => setShowAddChallenge(true)}
                  >
                    <Plus size={20} />
                    Add Challenge
                  </button>
                </div>
              )}

              {showAddChallenge && (user.role === 'PROFESSOR' || user.role === 'ADMIN') && (
                <div className="add-challenge-form">
                  <h3>Assign Challenge to Exam</h3>
                  <form onSubmit={handleAssignChallenge}>
                    <div className="form-group">
                      <label>Challenge *</label>
                      <select
                        value={newChallengeAssignment.challenge_id}
                        onChange={(e) =>
                          setNewChallengeAssignment({
                            ...newChallengeAssignment,
                            challenge_id: e.target.value,
                          })
                        }
                        required
                      >
                        <option value="">Select a challenge</option>
                        {allChallenges
                          .filter(
                            (ch) =>
                              !examChallenges.some(
                                (ec) => ec.challenge_id === ch.id
                              )
                          )
                          .map((challenge) => (
                            <option key={challenge.id} value={challenge.id}>
                              {challenge.title} ({challenge.difficulty})
                            </option>
                          ))}
                      </select>
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>Points *</label>
                        <input
                          type="number"
                          min="0"
                          value={newChallengeAssignment.points}
                          onChange={(e) =>
                            setNewChallengeAssignment({
                              ...newChallengeAssignment,
                              points: parseInt(e.target.value) || 0,
                            })
                          }
                          required
                        />
                      </div>
                      <div className="form-group">
                        <label>Order Index</label>
                        <input
                          type="number"
                          min="0"
                          value={newChallengeAssignment.order_index}
                          onChange={(e) =>
                            setNewChallengeAssignment({
                              ...newChallengeAssignment,
                              order_index: parseInt(e.target.value) || 0,
                            })
                          }
                        />
                      </div>
                    </div>
                    <div className="form-actions">
                      <button type="submit" className="btn-primary">
                        Assign
                      </button>
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => {
                          setShowAddChallenge(false);
                          setNewChallengeAssignment({
                            challenge_id: '',
                            points: 100,
                            order_index: 0,
                          });
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              )}

              <div className="exam-challenges-list">
                <h3>Assigned Challenges ({examChallenges.length})</h3>
                {examChallenges.length === 0 ? (
                  <p className="empty-message">No challenges assigned yet</p>
                ) : (
                  <div className="challenges-grid">
                    {examChallenges
                      .sort((a, b) => a.order_index - b.order_index)
                      .map((ec) => (
                        <div key={ec.challenge_id} className="challenge-item">
                          <div className="challenge-info">
                            <h4>{ec.title}</h4>
                            <p className="challenge-description">
                              {ec.description?.substring(0, 100)}
                              {ec.description?.length > 100 ? '...' : ''}
                            </p>
                            <div className="challenge-meta">
                              <span className="difficulty-badge">
                                {ec.difficulty}
                              </span>
                              <span className="points-badge">
                                {ec.points} points
                              </span>
                            </div>
                          </div>
                          {(user.role === 'PROFESSOR' ||
                            user.role === 'ADMIN') && (
                            <button
                              className="btn-danger"
                              onClick={() =>
                                handleUnassignChallenge(ec.challenge_id)
                              }
                              title="Remove challenge"
                            >
                              <Trash2 size={16} />
                            </button>
                          )}
                        </div>
                      ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Exam Modal */}
      {showEditForm && editingExam && (
        <div className="modal-overlay" onClick={() => setShowEditForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Edit Exam</h2>
              <button className="modal-close" onClick={() => setShowEditForm(false)}>
                <X size={24} />
              </button>
            </div>
            <form onSubmit={handleUpdateExam}>
              <div className="form-group">
                <label>Exam Title *</label>
                <input
                  type="text"
                  value={editingExam.title}
                  onChange={(e) => setEditingExam({ ...editingExam, title: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={editingExam.description || ''}
                  onChange={(e) => setEditingExam({ ...editingExam, description: e.target.value })}
                  rows={3}
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Start Time *</label>
                  <input
                    type="datetime-local"
                    value={editingExam.start_time ? new Date(editingExam.start_time).toISOString().slice(0, 16) : ''}
                    onChange={(e) => setEditingExam({ ...editingExam, start_time: new Date(e.target.value).toISOString() })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>End Time *</label>
                  <input
                    type="datetime-local"
                    value={editingExam.end_time ? new Date(editingExam.end_time).toISOString().slice(0, 16) : ''}
                    onChange={(e) => setEditingExam({ ...editingExam, end_time: new Date(e.target.value).toISOString() })}
                    required
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Duration (minutes) *</label>
                  <input
                    type="number"
                    min="1"
                    value={editingExam.duration_minutes}
                    onChange={(e) => setEditingExam({ ...editingExam, duration_minutes: parseInt(e.target.value) })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Max Attempts</label>
                  <input
                    type="number"
                    min="1"
                    value={editingExam.max_attempts}
                    onChange={(e) => setEditingExam({ ...editingExam, max_attempts: parseInt(e.target.value) })}
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Passing Score (0-100, optional)</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={editingExam.passing_score || ''}
                    onChange={(e) => setEditingExam({ ...editingExam, passing_score: e.target.value ? parseInt(e.target.value) : null })}
                  />
                </div>
                <div className="form-group">
                  <label>Status *</label>
                  <select
                    value={editingExam.status}
                    onChange={(e) => setEditingExam({ ...editingExam, status: e.target.value })}
                    required
                  >
                    <option value="draft">Draft</option>
                    <option value="scheduled">Scheduled</option>
                    <option value="active">Active</option>
                    <option value="completed">Completed</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>
              </div>
              <div className="form-actions">
                <button type="submit" className="btn-primary">Update</button>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => {
                    setShowEditForm(false);
                    setEditingExam(null);
                  }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Exams;

