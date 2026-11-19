import api from './api';

export const notificationsApi = {
  list: (params = {}) => api.get('/notifications', { params }).then((r) => r.data),
  markRead: (notificationId) =>
    api.patch(`/notifications/${notificationId}/read`).then((r) => r.data),
  markAllRead: () => api.patch('/notifications/read-all').then((r) => r.data),
  listJobLogs: (limit = 20) =>
    api.get('/notifications/job-logs', { params: { limit } }).then((r) => r.data),
};
