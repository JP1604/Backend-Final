import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { coursesAPI } from '../services/api';
import { BookOpen, Users, Code2, AlertCircle, Loader, Plus } from 'lucide-react';
import './Courses.css';

const Courses = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newCourse, setNewCourse] = useState({
    name: '',
    description: '',
    start_date: '',
    end_date: '',
    status: 'draft',
  });

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    fetchCourses();
  }, [user, navigate]);

  const fetchCourses = async () => {
    try {
      setLoading(true);
      const response = await coursesAPI.getAll();
      const data = Array.isArray(response.data) ? response.data : [];
      setCourses(data);
    } catch (err) {
      console.error('Error fetching courses:', err);
      setError(err.response?.data?.detail || 'Failed to load courses');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCourse = async (e) => {
    e.preventDefault();
    try {
      // Convert date strings to ISO format for the API
      // Only include dates if they are provided (not empty strings)
      const courseData = {
        name: newCourse.name.trim(),
        description: newCourse.description?.trim() || null,
      };
      
      // Only add dates if they are provided
      if (newCourse.start_date) {
        courseData.start_date = `${newCourse.start_date}T00:00:00.000Z`;
      }
      if (newCourse.end_date) {
        courseData.end_date = `${newCourse.end_date}T23:59:59.999Z`;
      }
      // Add status
      courseData.status = newCourse.status;
      
      await coursesAPI.create(courseData);
      setShowCreateForm(false);
      setNewCourse({ name: '', description: '', start_date: '', end_date: '', status: 'draft' });
      setError('');
      fetchCourses();
    } catch (err) {
      console.error('Error creating course:', err);
      const errorDetail = err.response?.data?.detail;
      if (Array.isArray(errorDetail)) {
        // Pydantic validation errors
        setError(errorDetail.map(e => e.msg || e).join(', '));
      } else {
        setError(errorDetail || 'Failed to create course');
      }
    }
  };

  if (!user) return null;

  const canCreateCourse = user.role === 'PROFESSOR' || user.role === 'ADMIN';

  return (
    <div className="courses-container">
      <div className="courses-header">
        <h1>Courses</h1>
        {canCreateCourse && (
          <button 
            className="btn-primary"
            onClick={() => setShowCreateForm(!showCreateForm)}
          >
            <Plus size={20} />
            Create Course
          </button>
        )}
      </div>

      {showCreateForm && canCreateCourse && (
        <div className="create-course-form">
          <h2>Create New Course</h2>
          <form onSubmit={handleCreateCourse}>
            <div className="form-group">
              <label>Course Name *</label>
              <input
                type="text"
                value={newCourse.name}
                onChange={(e) => setNewCourse({ ...newCourse, name: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={newCourse.description}
                onChange={(e) => setNewCourse({ ...newCourse, description: e.target.value })}
                rows={3}
              />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Start Date</label>
                <input
                  type="date"
                  value={newCourse.start_date}
                  onChange={(e) => setNewCourse({ ...newCourse, start_date: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>End Date</label>
                <input
                  type="date"
                  value={newCourse.end_date}
                  onChange={(e) => setNewCourse({ ...newCourse, end_date: e.target.value })}
                />
              </div>
            </div>
            <div className="form-group">
              <label>Status</label>
              <select
                value={newCourse.status}
                onChange={(e) => setNewCourse({ ...newCourse, status: e.target.value })}
              >
                <option value="draft">Draft</option>
                <option value="active">Active</option>
                <option value="completed">Completed</option>
                <option value="archived">Archived</option>
              </select>
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
          Loading courses...
        </div>
      ) : courses.length === 0 ? (
        <div className="empty-state">
          <BookOpen size={48} />
          <p>No courses available yet</p>
          {canCreateCourse && (
            <button 
              className="btn-primary"
              onClick={() => setShowCreateForm(true)}
            >
              Create Your First Course
            </button>
          )}
        </div>
      ) : (
        <div className="courses-grid">
          {courses.map((course) => (
            <div 
              key={course.id} 
              className="course-card"
              onClick={() => navigate(`/courses/${course.id}`)}
            >
              <div className="course-header">
                <h3>{course.name}</h3>
                <span className={`status-badge ${course.status?.toLowerCase()}`}>
                  {course.status}
                </span>
              </div>
              <p className="course-description">{course.description || 'No description'}</p>
              <div className="course-stats">
                <div className="stat">
                  <Users size={16} />
                  <span>{course.student_count || 0} students</span>
                </div>
                <div className="stat">
                  <Code2 size={16} />
                  <span>{course.challenge_count || 0} challenges</span>
                </div>
              </div>
              {course.start_date && (
                <div className="course-dates">
                  <small>
                    {new Date(course.start_date).toLocaleDateString()} - 
                    {course.end_date ? new Date(course.end_date).toLocaleDateString() : 'Ongoing'}
                  </small>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Courses;

