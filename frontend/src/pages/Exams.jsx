import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { examsAPI, coursesAPI } from '../services/api';
import { FileText, Clock, CheckCircle, AlertCircle, Loader, Plus } from 'lucide-react';
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
                {user.role === 'STUDENT' && exam.status === 'active' && (
                  <button 
                    className="btn-primary"
                    onClick={() => handleStartExam(exam.id)}
                  >
                    Start Exam
                  </button>
                )}
                {(user.role === 'PROFESSOR' || user.role === 'ADMIN') && (
                  <button 
                    className="btn-secondary"
                    onClick={() => navigate(`/exams/${exam.id}/results`)}
                  >
                    View Results
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Exams;

