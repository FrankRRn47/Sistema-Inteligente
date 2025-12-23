import axios from 'axios';

export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:5005';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ia_dashboard_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (resp) => resp,
  (error) => {
    const status = error.response?.status;
    const payload = error.response?.data || {};
    const rawMessage = payload.message || payload.msg || '';
    const normalized = typeof rawMessage === 'string' ? rawMessage.toLowerCase() : '';
    const shouldLogout =
      status === 401 ||
      (status === 422 && normalized.includes('subject must be a string'));

    if (shouldLogout) {
      window.dispatchEvent(
        new CustomEvent('auth:unauthorized', {
          detail: { reason: rawMessage || 'session-expired' },
        })
      );
    }
    return Promise.reject(error);
  }
);

export default api;
