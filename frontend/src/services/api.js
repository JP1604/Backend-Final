import axios from 'axios';

// Determinar la URL base del API:
// - Si VITE_API_URL está set (usado en build), usarlo
// - Si está en desarrollo local y localhost:5173 → usar localhost:8008
// - Si está en producción/docker → usar /api/ (proxy relativo a través de nginx)
let API_URL = import.meta?.env?.VITE_API_URL;

if (!API_URL) {
  // No environment variable set
  if (typeof window !== 'undefined') {
    if (window.location.hostname === 'localhost' && window.location.port === '5173') {
      // Vite dev server en localhost
      API_URL = 'http://localhost:8008';
    } else {
      // Production o Docker: usar ruta relativa a través de nginx
      API_URL = '/api';
    }
  }
}

console.log('API_URL:', API_URL);

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if it exists
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Auth API
export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (email, password, firstName, lastName) => 
    api.post('/auth/register', { 
      email, 
      password, 
      first_name: firstName, 
      last_name: lastName,
      role: 'STUDENT'
    }),
};

// Challenges API
export const challengesAPI = {
  getAll: () => api.get('/challenges'),
  getById: (id) => api.get(`/challenges/${id}`),
  create: (data) => api.post('/challenges', data),
  update: (id, data) => api.put(`/challenges/${id}`, data),
  delete: (id) => api.delete(`/challenges/${id}`),
};

// Users API
export const usersAPI = {
  getById: (id) => api.get(`/users/${id}`),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
  getAll: () => api.get('/users'),
};

// Submissions API
export const submissionsAPI = {
  submit: (challengeId, code, language) => 
    api.post('/submissions/submit', { challenge_id: challengeId, code, language }),
  getById: (id) => api.get(`/submissions/${id}`),
  getByChallenge: (challengeId) => api.get(`/submissions/challenge/${challengeId}`),
  getMy: () => api.get('/submissions/my'),
};

export default api;
