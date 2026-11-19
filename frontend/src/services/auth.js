import api from './api';

export const authApi = {
  register: (payload) => api.post('/auth/register', payload).then((r) => r.data),
  login: (payload) => api.post('/auth/login', payload).then((r) => r.data),
  getMe: () => api.get('/auth/me').then((r) => r.data),
  updateMe: (payload) => api.put('/auth/me', payload).then((r) => r.data),
  changePassword: (payload) => api.put('/auth/me/password', payload).then((r) => r.data),
  listUsers: () => api.get('/users').then((r) => r.data),
};
