import api from './api';

export const activityApi = {
  list: (params = {}) => api.get('/activity', { params }).then((r) => r.data),
};

export const dashboardApi = {
  getSummary: () => api.get('/dashboard/summary').then((r) => r.data),
  getProjectProgress: () => api.get('/dashboard/project-progress').then((r) => r.data),
};
