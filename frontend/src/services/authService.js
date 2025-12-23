import api from './api.js';

export async function registerUser(payload) {
  const { data } = await api.post('/register', payload);
  return data;
}

export async function loginUser(payload) {
  const { data } = await api.post('/login', payload);
  return data;
}

export async function fetchProfile() {
  const { data } = await api.get('/profile');
  return data;
}
