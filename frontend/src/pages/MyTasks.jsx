import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, Calendar, CheckSquare, Clock, Eye } from 'lucide-react';
import { tasksApi } from '../services/tasks';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/common/Button';
import {
  Card,
  EmptyState,
  ErrorBanner,
  LoadingSpinner,
  PriorityBadge,
  StatusBadge,
} from '../components/common/UI';
import { TaskDetailModal } from '../components/tasks/TaskDetailModal';
import { PRIORITIES, TASK_STATUSES } from '../utils/constants';
import { extractErrorMessage, formatDate, isDueSoon } from '../utils/formatters';

export function MyTasks() {
  const { refreshUnreadCount } = useAuth();
  const toast = useToast();

  const [tasks, setTasks] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [overdueOnly, setOverdueOnly] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);

  const loadMyTasks = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = {};
      if (statusFilter) params.status = statusFilter;
      if (priorityFilter) params.priority = priorityFilter;
      if (overdueOnly) params.overdue_only = true;
      const data = await tasksApi.listMyTasks(params);
      setTasks(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to load your assigned tasks.'));
    } finally {
      setLoading(false);
    }
  }, [statusFilter, priorityFilter, overdueOnly]);

  useEffect(() => {
    loadMyTasks();
  }, [loadMyTasks]);

  const handleStatusChange = async (taskId, newStatus) => {
    const previous = tasks;
    setTasks((curr) =>
      curr.map((t) => (t.id === taskId ? { ...t, status: newStatus } : t))
    );
    try {
      const updated = await tasksApi.updateStatus(taskId, newStatus);
      setTasks((curr) => curr.map((t) => (t.id === taskId ? updated : t)));
      if (selectedTask?.id === taskId) setSelectedTask(updated);
      toast.success(`Task status updated to "${newStatus}".`);
      refreshUnreadCount();
    } catch (err) {
      setTasks(previous);
      toast.error(extractErrorMessage(err, 'Failed to update status.'));
    }
  };

  const overdueCount = tasks.filter((t) => t.is_overdue).length;
  const upcomingCount = tasks.filter((t) => isDueSoon(t.due_date, t.status)).length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#101010]">My Tasks</h2>
          <p className="text-sm text-[#737373]">
            {total} {total === 1 ? 'task' : 'tasks'} assigned specifically to you
          </p>
        </div>
        <div className="flex items-center gap-2.5 text-xs font-semibold">
          {overdueCount > 0 && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-50 text-[#DC2626] border border-red-200">
              <AlertTriangle className="w-3.5 h-3.5" /> {overdueCount} Overdue
            </span>
          )}
          {upcomingCount > 0 && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-50 text-amber-800 border border-amber-200">
              <Clock className="w-3.5 h-3.5" /> {upcomingCount} Due Soon
            </span>
          )}
        </div>
      </div>

      {/* Filters */}
      <Card surface className="p-4 flex flex-wrap items-center gap-3">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-[#E5E5E5] bg-white px-3 py-2 text-sm text-[#101010]"
        >
          <option value="">All Statuses</option>
          {TASK_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>

        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="rounded-lg border border-[#E5E5E5] bg-white px-3 py-2 text-sm text-[#101010]"
        >
          <option value="">All Priorities</option>
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>

        <label className="inline-flex items-center gap-2 text-sm font-medium text-[#101010] cursor-pointer px-2">
          <input
            type="checkbox"
            checked={overdueOnly}
            onChange={(e) => setOverdueOnly(e.target.checked)}
            className="rounded accent-[#75C900] w-4 h-4"
          />
          <span>Overdue only</span>
        </label>

        {(statusFilter || priorityFilter || overdueOnly) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setStatusFilter('');
              setPriorityFilter('');
              setOverdueOnly(false);
            }}
          >
            Clear filters
          </Button>
        )}
      </Card>

      <ErrorBanner message={error} onRetry={loadMyTasks} />

      {loading ? (
        <LoadingSpinner label="Loading your tasks..." />
      ) : tasks.length === 0 ? (
        <EmptyState
          icon={CheckSquare}
          title="No assigned tasks found"
          description={
            statusFilter || priorityFilter || overdueOnly
              ? 'No tasks match your active filters.'
              : 'Tasks assigned to you across projects will appear here.'
          }
          action={
            <Link to="/projects">
              <Button variant="secondary" size="sm">
                Browse Projects
              </Button>
            </Link>
          }
        />
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#F5F5F5] border-b border-[#E5E5E5] text-[11px] font-bold uppercase tracking-wider text-[#737373]">
                  <th className="py-3 px-4">Task</th>
                  <th className="py-3 px-4">Project / Story</th>
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4">Due Date</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E5E5] text-sm">
                {tasks.map((task) => {
                  const soon = isDueSoon(task.due_date, task.status);
                  return (
                    <tr
                      key={task.id}
                      className={`hover:bg-[#F5F5F5]/60 transition-colors ${
                        task.is_overdue ? 'bg-red-50/40' : ''
                      }`}
                    >
                      <td className="py-3.5 px-4">
                        <button
                          type="button"
                          onClick={() => setSelectedTask(task)}
                          className="font-semibold text-[#101010] hover:text-[#66B000] text-left"
                        >
                          {task.title}
                        </button>
                      </td>
                      <td className="py-3.5 px-4">
                        <Link
                          to={`/projects/${task.project_id}`}
                          className="text-xs font-semibold text-[#101010] hover:underline block"
                        >
                          {task.project_name}
                        </Link>
                        <span className="text-xs text-[#737373]">
                          {task.user_story_title}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <PriorityBadge priority={task.priority} />
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1.5 text-xs">
                          <Calendar
                            className={`w-3.5 h-3.5 ${
                              task.is_overdue
                                ? 'text-[#DC2626]'
                                : soon
                                  ? 'text-[#F59E0B]'
                                  : 'text-[#737373]'
                            }`}
                          />
                          <span
                            className={
                              task.is_overdue
                                ? 'font-bold text-[#DC2626]'
                                : soon
                                  ? 'font-semibold text-amber-800'
                                  : 'text-[#101010]'
                            }
                          >
                            {formatDate(task.due_date)}
                          </span>
                          {task.is_overdue && (
                            <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded bg-red-100 text-[#DC2626]">
                              Overdue
                            </span>
                          )}
                          {!task.is_overdue && soon && (
                            <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded bg-amber-100 text-amber-800">
                              Soon
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <select
                          value={task.status}
                          onChange={(e) => handleStatusChange(task.id, e.target.value)}
                          className="rounded-lg border border-[#E5E5E5] bg-white px-2.5 py-1.5 text-xs font-semibold text-[#101010] focus:outline-none focus:ring-2 focus:ring-[#75C900]"
                        >
                          {TASK_STATUSES.map((st) => (
                            <option key={st} value={st}>
                              {st}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          type="button"
                          onClick={() => setSelectedTask(task)}
                          className="p-1.5 rounded-lg text-[#737373] hover:text-[#101010] hover:bg-[#F5F5F5]"
                          title="Inspect task"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      <TaskDetailModal
        open={Boolean(selectedTask)}
        task={selectedTask}
        onClose={() => setSelectedTask(null)}
        onStatusChange={handleStatusChange}
      />
    </div>
  );
}
