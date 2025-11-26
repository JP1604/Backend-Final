import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Code2, BookOpen, User, LogOut } from 'lucide-react';
import './Dashboard.css';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    challengesSolved: 0,
    submissionsTotal: 0,
  });

  useEffect(() => {
    if (!user) {
      navigate('/login');
    }
  }, [user, navigate]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!user) return null;

  return (
    <div className="dashboard-container">
      <div className="dashboard-content">
        <div className="dashboard-header">
          <div className="header-welcome">
            <h1>Welcome, {user.first_name}! 👋</h1>
            <p>Ready to solve some coding challenges?</p>
          </div>
          <button onClick={handleLogout} className="btn-logout">
            <LogOut size={20} />
            Logout
          </button>
        </div>

        <div className="dashboard-cards">
          <div 
            className="dashboard-card"
            onClick={() => navigate('/challenges')}
          >
            <div className="card-icon">
              <Code2 size={48} />
            </div>
            <h2>Challenges</h2>
            <p>Solve coding problems and improve your skills</p>
            <button className="btn-card">View Challenges →</button>
          </div>

          <div 
            className="dashboard-card"
            onClick={() => navigate('/submissions')}
          >
            <div className="card-icon">
              <BookOpen size={48} />
            </div>
            <h2>My Submissions</h2>
            <p>View your code submissions and scores</p>
            <button className="btn-card">View Submissions →</button>
          </div>

          <div 
            className="dashboard-card"
            onClick={() => navigate('/profile')}
          >
            <div className="card-icon">
              <User size={48} />
            </div>
            <h2>Profile</h2>
            <p>Manage your account and settings</p>
            <button className="btn-card">View Profile →</button>
          </div>
        </div>

        <div className="dashboard-stats">
          <h3>Your Stats</h3>
          <div className="stats-grid">
            <div className="stat">
              <span className="stat-value">0</span>
              <span className="stat-label">Challenges Solved</span>
            </div>
            <div className="stat">
              <span className="stat-value">0</span>
              <span className="stat-label">Total Submissions</span>
            </div>
            <div className="stat">
              <span className="stat-value">{user.role}</span>
              <span className="stat-label">Role</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
