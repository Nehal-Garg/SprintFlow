import api from './api';

export const projectsApi = {
  list: (params = {}) => api.get('/projects', { params }).then((r) => r.data),
  get: (projectId) => api.get(`/projects/${projectId}`).then((r) => r.data),
  create: (payload) => api.post('/projects', payload).then((r) => r.data),
  update: (projectId, payload) => api.put(`/projects/${projectId}`, payload).then((r) => r.data),
  remove: (projectId) => api.delete(`/projects/${projectId}`),
  addMember: (projectId, payload) =>
    api.post(`/projects/${projectId}/members`, payload).then((r) => r.data),
  removeMember: (projectId, userId) =>
    api.delete(`/projects/${projectId}/members/${userId}`),
};
