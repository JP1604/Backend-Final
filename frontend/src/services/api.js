import axios from 'axios';

// Determinar la URL base del API:
// IMPORTANTE: Cuando el código se ejecuta en el navegador, NUNCA debe usar nombres de servicios Docker
// como 'api:8000' porque el navegador no puede resolverlos. Siempre usar rutas relativas o localhost.
// - Si está en desarrollo local (Vite dev server en puerto 5173) → usar localhost:8008
// - Si está en producción/Docker (servido por Nginx) → usar /api (proxy relativo)

let API_URL = import.meta?.env?.VITE_API_URL;

// Detectar el entorno PRIMERO basado en window.location
if (typeof window !== 'undefined') {
  const hostname = window.location.hostname;
  const port = window.location.port;
  
  // Solo usar localhost:8008 si estamos en el servidor de desarrollo de Vite (puerto 5173)
  if (hostname === 'localhost' && port === '5173') {
    API_URL = 'http://localhost:8008';
  } else {
    // Cualquier otro caso (producción, Docker, etc.) → SIEMPRE usar ruta relativa
    // Nginx hará proxy de /api/* a http://api:8000/*
    // IGNORAR VITE_API_URL si contiene nombres de servicios Docker
    if (API_URL && (API_URL.includes('api:') || API_URL.includes('://api'))) {
      console.warn('VITE_API_URL contiene un nombre de servicio Docker interno. Forzando uso de /api');
      API_URL = '/api';
    } else if (!API_URL || API_URL === '') {
      API_URL = '/api';
    }
    // Si VITE_API_URL es válido (como '/api'), usarlo
  }
} else {
  // Fallback para SSR (aunque no lo usamos)
  API_URL = '/api';
}

// Asegurar que la URL base no termine con barra (excepto si es la raíz)
if (API_URL && API_URL !== '/' && API_URL.endsWith('/')) {
  API_URL = API_URL.slice(0, -1);
}

console.log('API_URL configurada:', API_URL);
if (typeof window !== 'undefined') {
  console.log('Window location:', `${window.location.hostname}:${window.location.port || '80'}`);
}

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

// Handle response errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log error for debugging
    if (error.code === 'ERR_NETWORK' || error.message?.includes('CORS')) {
      console.error('Network/CORS Error:', error);
      error.isNetworkError = true;
    } else if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
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
  getAll: () => api.get('/challenges/'),  // Agregar barra final para evitar redirecciones
  getById: (id) => api.get(`/challenges/${id}`),
  create: (data) => api.post('/challenges/', data),  // Agregar barra final
  update: (id, data) => api.put(`/challenges/${id}`, data),
  delete: (id) => api.delete(`/challenges/${id}`),
  getTestCases: (challengeId) => api.get(`/challenges/${challengeId}/test-cases`),
  createTestCase: (challengeId, data) => api.post(`/challenges/${challengeId}/test-cases`, data),
};

// Users API
export const usersAPI = {
  getById: (id) => api.get(`/users/${id}`),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
  getAll: () => api.get('/users/'),
};

// Submissions API
export const submissionsAPI = {
  submit: (challengeId, code) => 
    api.post('/submissions/submit', { challenge_id: challengeId, code }),
  getById: (id) => api.get(`/submissions/${id}`),
  getByChallenge: (challengeId) => api.get(`/submissions/challenge/${challengeId}`),
  getMy: () => api.get('/submissions/my'),
};

// Courses API
export const coursesAPI = {
  getAll: (teacherId, status) => {
    const params = new URLSearchParams();
    if (teacherId) params.append('teacher_id', teacherId);
    if (status) params.append('status_filter', status);
    const queryString = params.toString();
    const url = queryString ? `/courses/?${queryString}` : '/courses/';
    return api.get(url);
  },
  getById: (id) => api.get(`/courses/${id}`),
  create: (data) => api.post('/courses/', data),
  update: (id, data) => api.put(`/courses/${id}`, data),
  enrollStudent: (courseId, studentId) => 
    api.post(`/courses/${courseId}/students`, { student_id: studentId }),
  assignChallenge: (courseId, challengeId, orderIndex = 0) => 
    api.post(`/courses/${courseId}/challenges`, { challenge_id: challengeId, order_index: orderIndex }),
  getStudents: (courseId) => api.get(`/courses/${courseId}/students`),
  getChallenges: (courseId) => api.get(`/courses/${courseId}/challenges`),
};

// Exams API
export const examsAPI = {
  getAll: (courseId) => {
    const url = courseId ? `/exams/?course_id=${courseId}` : '/exams/';
    return api.get(url);
  },
  getById: (id) => api.get(`/exams/${id}`),
  create: (data) => api.post('/exams/', data),
  update: (id, data) => api.put(`/exams/${id}`, data),
  startAttempt: (examId) => api.post(`/exams/${examId}/start`),
  submitAttempt: (examId, attemptId, data) => 
    api.post(`/exams/${examId}/attempts/${attemptId}/submit`, data),
  getResults: (examId) => api.get(`/exams/${examId}/results`),
};

export default api;
