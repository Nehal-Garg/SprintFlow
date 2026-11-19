import { useCallback, useEffect, useState } from 'react';
import { Bell, Check, CheckCheck, Cpu, RefreshCw } from 'lucide-react';
import { notificationsApi } from '../services/notifications';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/common/Button';
import {
  Badge,
  Card,
  EmptyState,
  ErrorBanner,
  LoadingSpinner,
} from '../components/common/UI';
import { NOTIFICATION_TYPE_META } from '../utils/constants';
import { extractErrorMessage, formatDateTime, formatRelativeTime } from '../utils/formatters';

export function Notifications() {
  const { setUnreadCount } = useAuth();
  const toast = useToast();

  const [notifications, setNotifications] = useState([]);
  const [unreadCountLocal, setUnreadCountLocal] = useState(0);
  const [jobLogs, setJobLogs] = useState([]);
  const [showJobLogs, setShowJobLogs] = useState(false);

  const [unreadOnly, setUnreadOnly] = useState(false);
  const [typeFilter, setTypeFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [markingAll, setMarkingAll] = useState(false);

  const loadNotifications = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = { limit: 100 };
      if (unreadOnly) params.unread_only = true;
      if (typeFilter) params.notification_type = typeFilter;

      const [notifRes, logsRes] = await Promise.all([
        notificationsApi.list(params),
        notificationsApi.listJobLogs(15),
      ]);

      setNotifications(notifRes.items || []);
      setUnreadCountLocal(notifRes.unread_count || 0);
      setUnreadCount(notifRes.unread_count || 0);
      setJobLogs(logsRes || []);
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to load notifications.'));
    } finally {
      setLoading(false);
    }
  }, [unreadOnly, typeFilter, setUnreadCount]);

  useEffect(() => {
    loadNotifications();
  }, [loadNotifications]);

  const handleMarkRead = async (id) => {
    try {
      await notificationsApi.markRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCountLocal((c) => {
        const next = Math.max(0, c - 1);
        setUnreadCount(next);
        return next;
      });
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Could not mark notification as read.'));
    }
  };

  const handleMarkAllRead = async () => {
    setMarkingAll(true);
    try {
      const res = await notificationsApi.markAllRead();
      toast.success(res.message || 'All notifications marked as read.');
      await loadNotifications();
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Could not mark all notifications as read.'));
    } finally {
      setMarkingAll(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#101010]">Notifications</h2>
          <p className="text-sm text-[#737373]">
            {unreadCountLocal} unread · Generated persistently by task assignments and the FastAPI BackgroundTasks reminder workflow.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button variant="secondary" size="sm" onClick={loadNotifications} loading={loading}>
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </Button>
          <Button
            size="sm"
            onClick={handleMarkAllRead}
            loading={markingAll}
            disabled={unreadCountLocal === 0}
          >
            <CheckCheck className="w-4 h-4" /> Mark All Read
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card surface className="p-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="rounded-lg border border-[#E5E5E5] bg-white px-3 py-2 text-sm text-[#101010]"
          >
            <option value="">All Notification Types</option>
            <option value="upcoming_deadline">Upcoming Deadline</option>
            <option value="overdue_task">Overdue Task</option>
            <option value="task_assignment">Task Assignment</option>
          </select>

          <label className="inline-flex items-center gap-2 text-sm font-medium text-[#101010] cursor-pointer">
            <input
              type="checkbox"
              checked={unreadOnly}
              onChange={(e) => setUnreadOnly(e.target.checked)}
              className="rounded accent-[#75C900] w-4 h-4"
            />
            <span>Unread only</span>
          </label>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowJobLogs((v) => !v)}
        >
          <Cpu className="w-4 h-4" />
          {showJobLogs ? 'Hide Background Job Logs' : `Background Job Logs (${jobLogs.length})`}
        </Button>
      </Card>

      <ErrorBanner message={error} onRetry={loadNotifications} />

      {/* Optional Background Job Log Inspector */}
      {showJobLogs && (
        <div className="rounded-xl border border-neutral-800 bg-[#101010] text-white p-5 shadow-card">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Cpu className="w-4 h-4 text-[#75C900]" />
                FastAPI BackgroundTasks Execution Audit
              </h3>
              <p className="text-xs text-neutral-400">
                Recent deadline reminder runs, deduplication skips, and retry counts recorded in SQLite (background_job_logs).
              </p>
            </div>
          </div>
          {jobLogs.length === 0 ? (
            <p className="text-xs text-neutral-400">No background reminder runs logged yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-neutral-800 text-neutral-400">
                    <th className="py-2 pr-3">Task ID</th>
                    <th className="py-2 pr-3">Status</th>
                    <th className="py-2 pr-3">Attempts</th>
                    <th className="py-2 pr-3">Summary</th>
                    <th className="py-2">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-800">
                  {jobLogs.map((log) => (
                    <tr key={log.id}>
                      <td className="py-2 pr-3 font-mono text-neutral-300">
                        #{log.task_id ?? '—'}
                      </td>
                      <td className="py-2 pr-3">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                            log.status === 'completed'
                              ? 'bg-[#75C900]/20 text-[#75C900]'
                              : log.status === 'failed'
                                ? 'bg-red-900/50 text-red-300'
                                : 'bg-neutral-800 text-neutral-300'
                          }`}
                        >
                          {log.status}
                        </span>
                      </td>
                      <td className="py-2 pr-3 text-white font-semibold">{log.attempts}</td>
                      <td className="py-2 pr-3 text-neutral-200">
                        {log.result_summary || log.error_message || '—'}
                      </td>
                      <td className="py-2 text-neutral-400 whitespace-nowrap">
                        {formatDateTime(log.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Notifications List */}
      {loading ? (
        <LoadingSpinner label="Loading notifications..." />
      ) : notifications.length === 0 ? (
        <EmptyState
          icon={Bell}
          title="No notifications"
          description={
            unreadOnly || typeFilter
              ? 'No notifications match your selected filters.'
              : 'You are all caught up. Alerts appear automatically when tasks are assigned or deadlines approach.'
          }
        />
      ) : (
        <div className="space-y-3">
          {notifications.map((n) => {
            const meta = NOTIFICATION_TYPE_META[n.notification_type] || {
              label: n.notification_type,
              badgeClass: 'bg-neutral-100 text-[#101010] border-neutral-300',
            };
            return (
              <Card
                key={n.id}
                className={`p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-colors ${
                  !n.is_read ? 'border-l-4 border-l-[#75C900] bg-white' : 'bg-[#F5F5F5]/60'
                }`}
              >
                <div className="space-y-1.5 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge className={meta.badgeClass}>{meta.label}</Badge>
                    {!n.is_read && (
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#16A34A]">
                        Unread
                      </span>
                    )}
                    <span className="text-xs text-[#737373]">
                      {formatRelativeTime(n.created_at)} · {formatDateTime(n.created_at)}
                    </span>
                  </div>
                  <p
                    className={`text-sm ${
                      !n.is_read ? 'font-semibold text-[#101010]' : 'text-[#737373]'
                    }`}
                  >
                    {n.message}
                  </p>
                </div>

                {!n.is_read && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleMarkRead(n.id)}
                    className="shrink-0 self-start sm:self-center"
                  >
                    <Check className="w-3.5 h-3.5" /> Mark as Read
                  </Button>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
