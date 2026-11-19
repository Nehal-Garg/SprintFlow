import { useCallback, useEffect, useState } from 'react';
import { Calendar, FolderKanban, GripVertical, Layers, RefreshCw, User } from 'lucide-react';
import { projectsApi } from '../services/projects';
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
} from '../components/common/UI';
import { TaskDetailModal } from '../components/tasks/TaskDetailModal';
import { PRIORITIES, TASK_STATUSES } from '../utils/constants';
import { extractErrorMessage, formatDate } from '../utils/formatters';

const COLUMN_ACCENT = {
  'To Do': 'border-t-[#737373]',
  'In Progress': 'border-t-[#101010]',
  'In Review': 'border-t-[#F59E0B]',
  Done: 'border-t-[#75C900]',
};

export function KanbanBoard() {
  const { refreshUnreadCount } = useAuth();
  const toast = useToast();

  const [tasks, setTasks] = useState([]);
  const [projects, setProjects] = useState([]);
  const [projectFilter, setProjectFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [assigneeFilter, setAssigneeFilter] = useState('');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [draggedTaskId, setDraggedTaskId] = useState(null);
  const [dragOverCol, setDragOverCol] = useState(null);
  const [viewingTask, setViewingTask] = useState(null);

  const loadBoard = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const taskParams = { limit: 500 };
      if (projectFilter) taskParams.project_id = Number(projectFilter);
      if (priorityFilter) taskParams.priority = priorityFilter;
      if (assigneeFilter && assigneeFilter !== 'unassigned') {
        taskParams.assignee_id = Number(assigneeFilter);
      }

      const [projRes, tasksRes] = await Promise.all([
        projectsApi.list({ limit: 100 }),
        tasksApi.listAll(taskParams),
      ]);
      setProjects(projRes.items || []);
      const fetchedTasks = tasksRes.items || [];
      setTasks(
        assigneeFilter === 'unassigned'
          ? fetchedTasks.filter((t) => !t.assignee_id)
          : fetchedTasks
      );
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to load Kanban board.'));
    } finally {
      setLoading(false);
    }
  }, [projectFilter, priorityFilter, assigneeFilter]);

  const assigneeOptions = Array.from(
    new Map(
      projects
        .flatMap((p) => p.members || [])
        .map((m) => [m.user_id, { id: m.user_id, full_name: m.full_name }])
    ).values()
  ).sort((a, b) => a.full_name.localeCompare(b.full_name));

  useEffect(() => {
    loadBoard();
  }, [loadBoard]);

  const moveTaskToStatus = async (taskId, targetStatus) => {
    const existing = tasks.find((t) => t.id === taskId);
    if (!existing || existing.status === targetStatus) return;

    // Optimistic UI update with full snapshot preserved for rollback
    const snapshot = tasks;
    setTasks((prev) =>
      prev.map((t) =>
        t.id === taskId
          ? { ...t, status: targetStatus, is_overdue: targetStatus === 'Done' ? false : t.is_overdue }
          : t
      )
    );

    try {
      const updated = await tasksApi.updateStatus(taskId, targetStatus);
      setTasks((prev) => prev.map((t) => (t.id === taskId ? updated : t)));
      if (viewingTask?.id === taskId) setViewingTask(updated);
      toast.success(`Moved "${existing.title}" to ${targetStatus}.`);
      refreshUnreadCount();
    } catch (err) {
      // Revert UI immediately if backend update fails
      setTasks(snapshot);
      toast.error(
        `Update failed — reverted task: ${extractErrorMessage(err, 'Server rejected move.')}`
      );
    }
  };

  const handleDragStart = (e, taskId) => {
    setDraggedTaskId(taskId);
    e.dataTransfer.setData('text/plain', String(taskId));
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e, colStatus) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    if (dragOverCol !== colStatus) setDragOverCol(colStatus);
  };

  const handleDrop = (e, colStatus) => {
    e.preventDefault();
    const rawId = e.dataTransfer.getData('text/plain') || draggedTaskId;
    const taskId = Number(rawId);
    setDraggedTaskId(null);
    setDragOverCol(null);
    if (taskId) {
      moveTaskToStatus(taskId, colStatus);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#101010]">Kanban Board</h2>
          <p className="text-sm text-[#737373]">
            Drag and drop tasks across columns or use the card status selector — persisted live in SQLite.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <select
            value={projectFilter}
            onChange={(e) => setProjectFilter(e.target.value)}
            className="rounded-lg border border-[#E5E5E5] bg-white px-3 py-2 text-xs font-medium text-[#101010]"
          >
            <option value="">All Projects</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>

          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="rounded-lg border border-[#E5E5E5] bg-white px-3 py-2 text-xs font-medium text-[#101010]"
          >
            <option value="">All Priorities</option>
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>

          <select
            value={assigneeFilter}
            onChange={(e) => setAssigneeFilter(e.target.value)}
            className="rounded-lg border border-[#E5E5E5] bg-white px-3 py-2 text-xs font-medium text-[#101010]"
            aria-label="Filter Kanban by assignee"
          >
            <option value="">All Assignees</option>
            <option value="unassigned">Unassigned</option>
            {assigneeOptions.map((a) => (
              <option key={a.id} value={a.id}>
                {a.full_name}
              </option>
            ))}
          </select>

          {(projectFilter || priorityFilter || assigneeFilter) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setProjectFilter('');
                setPriorityFilter('');
                setAssigneeFilter('');
              }}
            >
              Clear
            </Button>
          )}

          <Button variant="secondary" size="sm" onClick={loadBoard} loading={loading}>
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </Button>
        </div>
      </div>

      <ErrorBanner message={error} onRetry={loadBoard} />

      {loading && tasks.length === 0 ? (
        <LoadingSpinner label="Loading Kanban board..." />
      ) : tasks.length === 0 ? (
        <EmptyState
          title="No tasks on the board"
          description="Create tasks under a project user story to start moving work across Kanban columns."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 items-start">
          {TASK_STATUSES.map((columnStatus) => {
            const columnTasks = tasks.filter((t) => t.status === columnStatus);
            const isOver = dragOverCol === columnStatus;

            return (
              <div
                key={columnStatus}
                onDragOver={(e) => handleDragOver(e, columnStatus)}
                onDragLeave={() => setDragOverCol(null)}
                onDrop={(e) => handleDrop(e, columnStatus)}
                className={`rounded-xl border border-t-4 ${COLUMN_ACCENT[columnStatus]} p-3.5 min-h-[460px] transition-colors ${
                  isOver
                    ? 'bg-[#75C900]/10 border-[#75C900]'
                    : 'bg-[#F5F5F5] border-[#E5E5E5]'
                }`}
              >
                <div className="flex items-center justify-between mb-3.5 px-1">
                  <h3 className="text-sm font-bold text-[#101010]">{columnStatus}</h3>
                  <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-white border border-[#E5E5E5] text-[#101010] tabular-nums">
                    {columnTasks.length}
                  </span>
                </div>

                <div className="space-y-3">
                  {columnTasks.map((task) => (
                    <Card
                      key={task.id}
                      className={`p-3.5 cursor-grab active:cursor-grabbing hover:border-[#101010] transition-all ${
                        draggedTaskId === task.id ? 'opacity-50 scale-[0.98]' : ''
                      }`}
                    >
                      <div
                        draggable
                        onDragStart={(e) => handleDragStart(e, task.id)}
                        onDragEnd={() => {
                          setDraggedTaskId(null);
                          setDragOverCol(null);
                        }}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <button
                            type="button"
                            onClick={() => setViewingTask(task)}
                            className="text-sm font-semibold text-[#101010] hover:text-[#66B000] text-left leading-snug"
                          >
                            {task.title}
                          </button>
                          <GripVertical className="w-4 h-4 text-[#737373] shrink-0 mt-0.5" />
                        </div>

                        <div className="mt-2 space-y-1 text-[11px] text-[#737373]">
                          <div className="flex items-center gap-1.5 truncate">
                            <FolderKanban className="w-3 h-3 shrink-0 text-[#101010]" />
                            <span className="truncate font-medium text-[#101010]">
                              {task.project_name}
                            </span>
                          </div>
                          <div className="flex items-center gap-1.5 truncate">
                            <Layers className="w-3 h-3 shrink-0" />
                            <span className="truncate">{task.user_story_title}</span>
                          </div>
                        </div>

                        <div className="flex flex-wrap items-center justify-between gap-2 mt-3 pt-2.5 border-t border-[#E5E5E5]">
                          <PriorityBadge priority={task.priority} />
                          <span
                            className={`inline-flex items-center gap-1 text-[11px] font-medium ${
                              task.is_overdue ? 'text-[#DC2626] font-bold' : 'text-[#737373]'
                            }`}
                          >
                            <Calendar className="w-3 h-3" />
                            {formatDate(task.due_date)}
                          </span>
                        </div>

                        <div className="flex items-center justify-between gap-2 mt-2.5">
                          <span className="inline-flex items-center gap-1 text-[11px] text-[#737373] truncate">
                            <User className="w-3 h-3 shrink-0" />
                            <span className="truncate">
                              {task.assignee_name || 'Unassigned'}
                            </span>
                          </span>
                          <select
                            value={task.status}
                            onChange={(e) => moveTaskToStatus(task.id, e.target.value)}
                            className="rounded border border-[#E5E5E5] bg-[#F5F5F5] px-1.5 py-0.5 text-[11px] font-semibold text-[#101010] focus:outline-none focus:ring-1 focus:ring-[#75C900]"
                            aria-label={`Move ${task.title}`}
                          >
                            {TASK_STATUSES.map((st) => (
                              <option key={st} value={st}>
                                {st}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>
                    </Card>
                  ))}

                  {columnTasks.length === 0 && (
                    <div className="rounded-lg border border-dashed border-[#E5E5E5] py-8 text-center text-xs text-[#737373]">
                      Drop a task here
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <TaskDetailModal
        open={Boolean(viewingTask)}
        task={viewingTask}
        onClose={() => setViewingTask(null)}
        onStatusChange={moveTaskToStatus}
      />
    </div>
  );
}
