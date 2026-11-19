import api from './api';

export const tasksApi = {
  listByStory: (storyId, params = {}) =>
    api.get(`/stories/${storyId}/tasks`, { params }).then((r) => r.data),
  listAll: (params = {}) => api.get('/tasks', { params }).then((r) => r.data),
  listMyTasks: (params = {}) => api.get('/my-tasks', { params }).then((r) => r.data),
  get: (taskId) => api.get(`/tasks/${taskId}`).then((r) => r.data),
  create: (storyId, payload) =>
    api.post(`/stories/${storyId}/tasks`, payload).then((r) => r.data),
  update: (taskId, payload) => api.put(`/tasks/${taskId}`, payload).then((r) => r.data),
  updateStatus: (taskId, status) =>
    api.patch(`/tasks/${taskId}/status`, { status }).then((r) => r.data),
  remove: (taskId) => api.delete(`/tasks/${taskId}`),
};
