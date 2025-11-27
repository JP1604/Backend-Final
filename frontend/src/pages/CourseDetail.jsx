import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { coursesAPI, challengesAPI, usersAPI } from '../services/api';
import { ArrowLeft, Users, Code2, AlertCircle, Loader, Plus, UserPlus, Edit2, X } from 'lucide-react';
import './CourseDetail.css';

const CourseDetail = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { courseId } = useParams();
  const [course, setCourse] = useState(null);
  const [challenges, setChallenges] = useState([]);
  const [students, setStudents] = useState([]);
  const [allStudents, setAllStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateChallenge, setShowCreateChallenge] = useState(false);
  const [showAddStudent, setShowAddStudent] = useState(false);
  const [showEditCourse, setShowEditCourse] = useState(false);
  const [newChallenge, setNewChallenge] = useState({
    title: '',
    description: '',
    difficulty: 'easy',
    tags: '',
    time_limit: 1000,
    memory_limit: 256,
    language: 'python',
  });
  const [selectedStudentId, setSelectedStudentId] = useState('');
  const [editCourseData, setEditCourseData] = useState({
    name: '',
    description: '',
    status: 'draft',
  });

  const isTeacher = user?.role === 'PROFESSOR' || user?.role === 'ADMIN';
  const canManage = isTeacher && course && (course.teacher_id === user.id || user.role === 'ADMIN');

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    fetchCourseDetails();
    if (isTeacher) {
      fetchAllStudents();
    }
  }, [user, navigate, courseId, isTeacher]);

  const fetchCourseDetails = async () => {
    try {
      setLoading(true);
      const promises = [
        coursesAPI.getById(courseId),
        coursesAPI.getChallenges(courseId),
        coursesAPI.getStudents(courseId), // All users (students, teachers, admins) can view students
      ];
      
      const results = await Promise.all(promises);
      const [courseResp, challengesResp, studentsResp] = results;
      
      setCourse(courseResp.data || courseResp);
      // Handle challenges response - it can be an array directly or wrapped in data
      const challengesData = challengesResp.data || challengesResp;
      setChallenges(Array.isArray(challengesData) ? challengesData : []);
      // Handle students response - all enrolled users can view
      if (studentsResp) {
        const studentsData = studentsResp.data || studentsResp;
        setStudents(Array.isArray(studentsData) ? studentsData : []);
      } else {
        setStudents([]);
      }
      
      if (courseResp.data || courseResp) {
        const courseData = courseResp.data || courseResp;
        setEditCourseData({
          name: courseData.name || '',
          description: courseData.description || '',
          status: courseData.status?.toLowerCase() || 'draft',
        });
      }
    } catch (err) {
      console.error('Error fetching course details:', err);
      setError(err.response?.data?.detail || 'Failed to load course details');
    } finally {
      setLoading(false);
    }
  };

  const fetchAllStudents = async () => {
    try {
      const response = await usersAPI.getAll();
      const users = Array.isArray(response.data) ? response.data : [];
      setAllStudents(users.filter(u => u.role === 'STUDENT'));
    } catch (err) {
      console.error('Error fetching students:', err);
    }
  };

  const handleCreateChallenge = async (e) => {
    e.preventDefault();
    try {
      // Convert difficulty to match enum (Easy, Medium, Hard)
      const difficultyMap = {
        'easy': 'Easy',
        'medium': 'Medium',
        'hard': 'Hard'
      };
      
      const challengeData = {
        title: newChallenge.title.trim(),
        description: newChallenge.description.trim(),
        difficulty: difficultyMap[newChallenge.difficulty] || newChallenge.difficulty,
        tags: newChallenge.tags.split(',').map(t => t.trim()).filter(t => t),
        time_limit: parseInt(newChallenge.time_limit),
        memory_limit: parseInt(newChallenge.memory_limit),
        language: newChallenge.language,
        course_id: courseId,
      };
      
      const response = await challengesAPI.create(challengeData);
      const createdChallenge = response.data || response;
      
      console.log('Challenge created:', createdChallenge);
      
      // Automatically assign the challenge to the course
      if (createdChallenge.id) {
        try {
          console.log('Assigning challenge', createdChallenge.id, 'to course', courseId);
          const assignResponse = await coursesAPI.assignChallenge(courseId, createdChallenge.id, 0);
          console.log('Assignment response:', assignResponse);
        } catch (assignErr) {
          console.error('Challenge created but could not be assigned to course:', assignErr);
          setError(assignErr.response?.data?.detail || 'Challenge created but could not be assigned to course');
          // Still refresh to show the challenge even if assignment failed
        }
      } else {
        console.error('Challenge created but no ID returned:', createdChallenge);
        setError('Challenge created but no ID returned');
      }
      
      setShowCreateChallenge(false);
      setNewChallenge({
        title: '',
        description: '',
        difficulty: 'easy',
        tags: '',
        time_limit: 1000,
        memory_limit: 256,
        language: 'python',
      });
      
      // Wait a bit before refreshing to ensure the assignment is committed
      setTimeout(() => {
        fetchCourseDetails();
      }, 1000);
    } catch (err) {
      console.error('Error creating challenge:', err);
      const errorDetail = err.response?.data?.detail;
      if (Array.isArray(errorDetail)) {
        setError(errorDetail.map(e => e.msg || e).join(', '));
      } else {
        setError(errorDetail || 'Failed to create challenge');
      }
    }
  };

  const handleAddStudent = async (e) => {
    e.preventDefault();
    if (!selectedStudentId) {
      setError('Please select a student');
      return;
    }
    try {
      await coursesAPI.enrollStudent(courseId, selectedStudentId);
      setShowAddStudent(false);
      setSelectedStudentId('');
      setError('');
      fetchCourseDetails();
    } catch (err) {
      console.error('Error adding student:', err);
      setError(err.response?.data?.detail || 'Failed to add student');
    }
  };

  const handleEditCourse = async (e) => {
    e.preventDefault();
    try {
      const updateData = {
        name: editCourseData.name.trim(),
        description: editCourseData.description?.trim() || null,
        status: editCourseData.status,
      };
      
      await coursesAPI.update(courseId, updateData);
      setShowEditCourse(false);
      setError('');
      fetchCourseDetails();
    } catch (err) {
      console.error('Error updating course:', err);
      const errorDetail = err.response?.data?.detail;
      if (Array.isArray(errorDetail)) {
        setError(errorDetail.map(e => e.msg || e).join(', '));
      } else {
        setError(errorDetail || 'Failed to update course');
      }
    }
  };

  if (!user) return null;

  return (
    <div className="course-detail-container">
      <button 
        className="btn-back"
        onClick={() => navigate('/courses')}
      >
        <ArrowLeft size={20} />
        Back to Courses
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
          Loading course details...
        </div>
      ) : course ? (
        <>
          <div className="course-detail-header">
            <div>
              <h1>{course.name}</h1>
              <span className={`status-badge ${course.status?.toLowerCase()}`}>
                {course.status}
              </span>
            </div>
            {canManage && (
              <button
                className="btn-edit"
                onClick={() => setShowEditCourse(true)}
              >
                <Edit2 size={18} />
                Edit Course
              </button>
            )}
          </div>

          <p className="course-description">{course.description || 'No description'}</p>

          <div className="course-sections">
            <div className="section">
              <div className="section-header">
                <h2>
                  <Code2 size={24} />
                  Challenges ({challenges.length})
                </h2>
                {canManage && (
                  <button
                    className="btn-add"
                    onClick={() => setShowCreateChallenge(true)}
                  >
                    <Plus size={18} />
                    Add Challenge
                  </button>
                )}
              </div>
              {challenges.length === 0 ? (
                <p className="empty-section">No challenges assigned yet</p>
              ) : (
                <div className="challenges-list">
                  {challenges.map((challenge) => (
                    <div
                      key={challenge.id}
                      className="challenge-card"
                      onClick={() => navigate(`/challenges/${challenge.id}`)}
                    >
                      <h3>{challenge.title}</h3>
                      <span className={`difficulty-badge ${challenge.difficulty?.toLowerCase()}`}>
                        {challenge.difficulty}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="section">
              <div className="section-header">
                <h2>
                  <Users size={24} />
                  Students ({students.length})
                </h2>
                {canManage && (
                  <button
                    className="btn-add"
                    onClick={() => setShowAddStudent(true)}
                  >
                    <UserPlus size={18} />
                    Add Student
                  </button>
                )}
              </div>
              {students.length === 0 ? (
                <p className="empty-section">No students enrolled yet</p>
              ) : (
                <div className="students-list">
                  {students.map((student) => (
                    <div key={student.id} className="student-card">
                      <div className="student-avatar">
                        {student.first_name?.[0]?.toUpperCase() || 'S'}
                      </div>
                      <div className="student-info">
                        <h4>{student.first_name} {student.last_name}</h4>
                        <p>{student.email}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Create Challenge Modal */}
          {showCreateChallenge && (
            <div className="modal-overlay" onClick={() => setShowCreateChallenge(false)}>
              <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                  <h3>Create Challenge</h3>
                  <button className="btn-close" onClick={() => setShowCreateChallenge(false)}>
                    <X size={20} />
                  </button>
                </div>
                <form onSubmit={handleCreateChallenge}>
                  <div className="form-group">
                    <label>Title *</label>
                    <input
                      type="text"
                      value={newChallenge.title}
                      onChange={(e) => setNewChallenge({ ...newChallenge, title: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Description *</label>
                    <textarea
                      value={newChallenge.description}
                      onChange={(e) => setNewChallenge({ ...newChallenge, description: e.target.value })}
                      rows={5}
                      required
                    />
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Difficulty *</label>
                      <select
                        value={newChallenge.difficulty}
                        onChange={(e) => setNewChallenge({ ...newChallenge, difficulty: e.target.value })}
                        required
                      >
                        <option value="easy">Easy</option>
                        <option value="medium">Medium</option>
                        <option value="hard">Hard</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Tags (comma-separated)</label>
                      <input
                        type="text"
                        value={newChallenge.tags}
                        onChange={(e) => setNewChallenge({ ...newChallenge, tags: e.target.value })}
                        placeholder="array, sorting, algorithm"
                      />
                    </div>
                  </div>
                  <div className="form-group">
                    <label>Programming Language *</label>
                    <select
                      value={newChallenge.language}
                      onChange={(e) => setNewChallenge({ ...newChallenge, language: e.target.value })}
                      required
                    >
                      <option value="python">Python</option>
                      <option value="nodejs">Node.js (JavaScript)</option>
                      <option value="java">Java</option>
                      <option value="cpp">C++</option>
                    </select>
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Time Limit (ms) *</label>
                      <input
                        type="number"
                        value={newChallenge.time_limit}
                        onChange={(e) => setNewChallenge({ ...newChallenge, time_limit: e.target.value })}
                        min="100"
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label>Memory Limit (MB) *</label>
                      <input
                        type="number"
                        value={newChallenge.memory_limit}
                        onChange={(e) => setNewChallenge({ ...newChallenge, memory_limit: e.target.value })}
                        min="1"
                        required
                      />
                    </div>
                  </div>
                  <div className="form-actions">
                    <button type="submit" className="btn-primary">Create</button>
                    <button type="button" className="btn-secondary" onClick={() => setShowCreateChallenge(false)}>
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* Add Student Modal */}
          {showAddStudent && (
            <div className="modal-overlay" onClick={() => setShowAddStudent(false)}>
              <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                  <h3>Add Student</h3>
                  <button className="btn-close" onClick={() => setShowAddStudent(false)}>
                    <X size={20} />
                  </button>
                </div>
                <form onSubmit={handleAddStudent}>
                  <div className="form-group">
                    <label>Select Student *</label>
                    <select
                      value={selectedStudentId}
                      onChange={(e) => setSelectedStudentId(e.target.value)}
                      required
                    >
                      <option value="">-- Select a student --</option>
                      {allStudents
                        .filter(s => !students.some(enrolled => enrolled.id === s.id))
                        .map(student => (
                          <option key={student.id} value={student.id}>
                            {student.first_name} {student.last_name} ({student.email})
                          </option>
                        ))}
                    </select>
                  </div>
                  <div className="form-actions">
                    <button type="submit" className="btn-primary">Add Student</button>
                    <button type="button" className="btn-secondary" onClick={() => setShowAddStudent(false)}>
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* Edit Course Modal */}
          {showEditCourse && (
            <div className="modal-overlay" onClick={() => setShowEditCourse(false)}>
              <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                  <h3>Edit Course</h3>
                  <button className="btn-close" onClick={() => setShowEditCourse(false)}>
                    <X size={20} />
                  </button>
                </div>
                <form onSubmit={handleEditCourse}>
                  <div className="form-group">
                    <label>Name *</label>
                    <input
                      type="text"
                      value={editCourseData.name}
                      onChange={(e) => setEditCourseData({ ...editCourseData, name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Description</label>
                    <textarea
                      value={editCourseData.description}
                      onChange={(e) => setEditCourseData({ ...editCourseData, description: e.target.value })}
                      rows={4}
                    />
                  </div>
                  <div className="form-group">
                    <label>Status *</label>
                    <select
                      value={editCourseData.status}
                      onChange={(e) => setEditCourseData({ ...editCourseData, status: e.target.value })}
                      required
                    >
                      <option value="draft">Draft</option>
                      <option value="active">Active</option>
                      <option value="completed">Completed</option>
                      <option value="archived">Archived</option>
                    </select>
                  </div>
                  <div className="form-actions">
                    <button type="submit" className="btn-primary">Save Changes</button>
                    <button type="button" className="btn-secondary" onClick={() => setShowEditCourse(false)}>
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="empty-state">
          <p>Course not found</p>
        </div>
      )}
    </div>
  );
};

export default CourseDetail;
