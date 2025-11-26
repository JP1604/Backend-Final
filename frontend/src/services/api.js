import axios from 'axios';

const API_URL = 'http://localhost:8008';

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

// Submissions API
export const submissionsAPI = {
  submit: (challengeId, code, language) => 
    api.post('/submissions/submit', { challenge_id: challengeId, code, language }),
  getById: (id) => api.get(`/submissions/${id}`),
  getByChallenge: (challengeId) => api.get(`/submissions/challenge/${challengeId}`),
  getMy: () => api.get('/submissions/my'),
};

export default api;
