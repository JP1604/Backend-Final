import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { usersAPI } from '../services/api';
import { Save, AlertCircle, CheckCircle, Eye, EyeOff, LogOut } from 'lucide-react';
import './Profile.css';

const Profile = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    password_confirm: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    const fetchUserData = async () => {
      try {
        setLoading(true);
        const response = await usersAPI.getById(user.id);
        const userData = response.data || response;
        
        setFormData({
          first_name: userData.first_name || '',
          last_name: userData.last_name || '',
          email: userData.email || '',
          password: '',
          password_confirm: '',
        });
      } catch (err) {
        console.error('Error fetching user data:', err);
        setError('Failed to load profile data');
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, [user, navigate]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    // Validate
    if (!formData.first_name.trim() || !formData.last_name.trim()) {
      setError('First name and last name are required');
      return;
    }

    if (formData.password && formData.password !== formData.password_confirm) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password && formData.password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    try {
      setSaving(true);
      const updateData = {
        first_name: formData.first_name,
        last_name: formData.last_name,
      };

      if (formData.password) {
        updateData.password = formData.password;
      }

      const response = await usersAPI.update(user.id, updateData);
      
      setSuccess('Profile updated successfully!');
      setFormData(prev => ({
        ...prev,
        password: '',
        password_confirm: '',
      }));
    } catch (err) {
      console.error('Error updating profile:', err);
      setError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!user) return null;

  return (
    <div className="profile-container">
      <div className="profile-wrapper">
        <div className="profile-header">
          <h1>My Profile</h1>
          <p className="profile-subtitle">Manage your account information</p>
        </div>

        {loading ? (
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Loading profile...</p>
          </div>
        ) : (
          <div className="profile-content">
            {/* User Info Section */}
            <div className="profile-section">
              <h2>Account Information</h2>
              
              <form onSubmit={handleSubmit} className="profile-form">
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="first_name">First Name</label>
                    <input
                      type="text"
                      id="first_name"
                      name="first_name"
                      value={formData.first_name}
                      onChange={handleChange}
                      className="form-input"
                      placeholder="First name"
                      disabled={saving}
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="last_name">Last Name</label>
                    <input
                      type="text"
                      id="last_name"
                      name="last_name"
                      value={formData.last_name}
                      onChange={handleChange}
                      className="form-input"
                      placeholder="Last name"
                      disabled={saving}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="email">Email</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    className="form-input"
                    placeholder="Email"
                    disabled
                  />
                  <p className="form-help">Email cannot be changed</p>
                </div>

                <hr className="form-divider" />

                <h3>Change Password (Optional)</h3>

                <div className="form-group">
                  <label htmlFor="password">New Password</label>
                  <div className="password-input-group">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      id="password"
                      name="password"
                      value={formData.password}
                      onChange={handleChange}
                      className="form-input"
                      placeholder="Leave blank to keep current password"
                      disabled={saving}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="toggle-password"
                      tabIndex="-1"
                    >
                      {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                    </button>
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="password_confirm">Confirm Password</label>
                  <div className="password-input-group">
                    <input
                      type={showConfirm ? 'text' : 'password'}
                      id="password_confirm"
                      name="password_confirm"
                      value={formData.password_confirm}
                      onChange={handleChange}
                      className="form-input"
                      placeholder="Confirm new password"
                      disabled={saving}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirm(!showConfirm)}
                      className="toggle-password"
                      tabIndex="-1"
                    >
                      {showConfirm ? <EyeOff size={20} /> : <Eye size={20} />}
                    </button>
                  </div>
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
                  className="btn-save"
                  disabled={saving}
                >
                  {saving ? (
                    <>
                      <div className="spinner-sm"></div>
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save size={20} />
                      Save Changes
                    </>
                  )}
                </button>
              </form>
            </div>

            {/* Account Section */}
            <div className="profile-section">
              <h2>Account</h2>
              <div className="account-info">
                <div className="info-item">
                  <span className="info-label">Role</span>
                  <span className="info-value role-badge">{user.role || 'user'}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">User ID</span>
                  <span className="info-value">{user.id}</span>
                </div>
              </div>

              <button onClick={handleLogout} className="btn-logout">
                <LogOut size={20} />
                Logout
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Profile;
