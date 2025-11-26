import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      // Decode JWT to get user info (simple decode, not verification)
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setUser({ id: payload.sub, email: payload.email, role: payload.role });
      } catch (error) {
        console.error('Invalid token:', error);
        localStorage.removeItem('token');
        setToken(null);
      }
    }
    setLoading(false);
  }, [token]);

  const login = async (email, password) => {
    try {
      // Llamar al endpoint real del backend
      const response = await authAPI.login(email, password);
      
      // axios devuelve la respuesta en response.data
      const data = response.data || response;
      
      // Guardar el token en localStorage
      localStorage.setItem('token', data.access_token);
      setToken(data.access_token);
      
      // Guardar info del usuario
      setUser({
        id: data.user.id,
        email: data.user.email,
        role: data.user.role,
        first_name: data.user.first_name,
        last_name: data.user.last_name,
      });
      
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const register = async (email, password, firstName, lastName) => {
    try {
      // Llamar al endpoint real del backend
      const response = await authAPI.register(email, password, firstName, lastName);
      
      // axios devuelve la respuesta en response.data
      // El registro es exitoso, pero no guardamos token
      // El usuario debe loguearse después
      return { success: true };
    } catch (error) {
      console.error('Register error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!token,
    isAdmin: user?.role === 'admin',
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
