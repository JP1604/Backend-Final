import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Code2, 
  LogOut, 
  User, 
  Home, 
  Trophy, 
  FileCode,
  Settings,
  Menu,
  X,
  GraduationCap,
  FileText
} from 'lucide-react';
import { useState } from 'react';
import './Navbar.css';

const Navbar = () => {
  const { user, logout, isAuthenticated, isAdmin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
    setMobileMenuOpen(false);
  };

  const isActive = (path) => location.pathname === path;

  const NavLink = ({ to, children, icon: Icon }) => (
    <Link
      to={to}
      className={`nav-link ${isActive(to) ? 'active' : ''}`}
      onClick={() => setMobileMenuOpen(false)}
    >
      {Icon && <Icon size={18} />}
      <span>{children}</span>
    </Link>
  );

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo" onClick={() => setMobileMenuOpen(false)}>
          <Code2 size={28} className="logo-icon" />
          <span className="logo-text">
            Code<span className="logo-accent">Judge</span>
          </span>
        </Link>

        <button 
          className="mobile-menu-button"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle menu"
        >
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>

        <div className={`navbar-menu ${mobileMenuOpen ? 'mobile-open' : ''}`}>
          {isAuthenticated ? (
            <>
              <div className="nav-links">
                <NavLink to="/dashboard" icon={Home}>Dashboard</NavLink>
                <NavLink to="/challenges" icon={Trophy}>Challenges</NavLink>
                <NavLink to="/courses" icon={GraduationCap}>Courses</NavLink>
                <NavLink to="/exams" icon={FileText}>Exams</NavLink>
                <NavLink to="/submissions" icon={FileCode}>My Submissions</NavLink>
                {isAdmin && (
                  <NavLink to="/admin" icon={Settings}>Admin</NavLink>
                )}
              </div>

              <div className="nav-actions">
                <Link 
                  to="/profile" 
                  className="user-info"
                  onClick={() => setMobileMenuOpen(false)}
                  title="View Profile"
                >
                  <div className="user-avatar">
                    {user?.first_name ? user.first_name.charAt(0).toUpperCase() : <User size={18} />}
                  </div>
                  <div className="user-details">
                    <div className="user-name">{user?.first_name || 'User'}</div>
                    <div className="user-email">{user?.email}</div>
                  </div>
                </Link>
                <button onClick={handleLogout} className="btn-logout">
                  <LogOut size={18} />
                  <span>Logout</span>
                </button>
              </div>
            </>
          ) : (
            <div className="nav-actions">
              <Link 
                to="/login" 
                className="btn-secondary"
                onClick={() => setMobileMenuOpen(false)}
              >
                Login
              </Link>
              <Link 
                to="/register" 
                className="btn-primary"
                onClick={() => setMobileMenuOpen(false)}
              >
                Sign Up
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
