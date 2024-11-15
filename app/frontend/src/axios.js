import axios from 'axios';

// Create axios instance with custom config
const instance = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  withCredentials: true, // Important for cookies/sessions
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor
instance.interceptors.request.use(
  (config) => {
    // Add token to headers if it exists
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor
instance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and user data on authentication error
      localStorage.removeItem('token');
      delete instance.defaults.headers.common['Authorization'];
    }
    return Promise.reject(error);
  }
);

export default instance;
