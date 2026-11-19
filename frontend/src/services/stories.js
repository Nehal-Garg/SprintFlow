import api from './api';

export const storiesApi = {
  listByProject: (projectId, params = {}) =>
    api.get(`/projects/${projectId}/stories`, { params }).then((r) => r.data),
  get: (storyId) => api.get(`/stories/${storyId}`).then((r) => r.data),
  create: (projectId, payload) =>
    api.post(`/projects/${projectId}/stories`, payload).then((r) => r.data),
  update: (storyId, payload) =>
    api.put(`/stories/${storyId}`, payload).then((r) => r.data),
  remove: (storyId) => api.delete(`/stories/${storyId}`),
};
