import { useCallback, useEffect, useState } from 'react';
import { Activity, RefreshCw } from 'lucide-react';
import { activityApi } from '../services/dashboard';
import { projectsApi } from '../services/projects';
import { Button } from '../components/common/Button';
import {
  Badge,
  Card,
  EmptyState,
  ErrorBanner,
  LoadingSpinner,
} from '../components/common/UI';
import { ACTIVITY_ACTION_LABELS } from '../utils/constants';
import { extractErrorMessage, formatDateTime, formatRelativeTime } from '../utils/formatters';

export function ActivityLog() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [projects, setProjects] = useState([]);
  const [projectFilter, setProjectFilter] = useState('');
  const [entityFilter, setEntityFilter] = useState('');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadActivities = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = { limit: 100 };
      if (projectFilter) params.project_id = Number(projectFilter);
      if (entityFilter) params.entity_type = entityFilter;

      const [actRes, projRes] = await Promise.all([
        activityApi.list(params),
        projectsApi.list({ limit: 100 }),
      ]);
      setItems(actRes.items || []);
      setTotal(actRes.total || 0);
      setProjects(projRes.items || []);
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to load activity log.'));
    } finally {
      setLoading(false);
    }
  }, [projectFilter, entityFilter]);

  useEffect(() => {
    loadActivities();
  }, [loadActivities]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#101010]">Activity Log</h2>
          <p className="text-sm text-[#737373]">
            {total} chronological audit {total === 1 ? 'event' : 'events'} across your projects, user stories, and tasks
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={loadActivities} loading={loading}>
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card surface className="p-4 flex flex-wrap items-center gap-3">
        <select
          value={projectFilter}
          onChange={(e) => setProjectFilter(e.target.value)}
          className="rounded-lg border border-[#E5E5E5] bg-white px-3 py-2 text-sm text-[#101010]"
        >
          <option value="">All Projects</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>

        <select
          value={entityFilter}
          onChange={(e) => setEntityFilter(e.target.value)}
          className="rounded-lg border border-[#E5E5E5] bg-white px-3 py-2 text-sm text-[#101010]"
        >
          <option value="">All Entity Types</option>
          <option value="project">Projects</option>
          <option value="user_story">User Stories</option>
          <option value="task">Tasks</option>
        </select>

        {(projectFilter || entityFilter) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setProjectFilter('');
              setEntityFilter('');
            }}
          >
            Clear filters
          </Button>
        )}
      </Card>

      <ErrorBanner message={error} onRetry={loadActivities} />

      {loading ? (
        <LoadingSpinner label="Loading activity timeline..." />
      ) : items.length === 0 ? (
        <EmptyState
          icon={Activity}
          title="No activity recorded"
          description="Actions such as creating projects, user stories, tasks, assignments, and status updates appear here."
        />
      ) : (
        <Card className="p-5">
          <ol className="relative border-l-2 border-[#E5E5E5] ml-2.5 space-y-5">
            {items.map((act) => {
              const actionLabel = ACTIVITY_ACTION_LABELS[act.action] || act.action;
              const isCompleted = act.action === 'task_completed';
              const isDeleted = act.action.endsWith('_deleted');

              const badgeStyle = isCompleted
                ? 'bg-[#75C900]/20 text-[#101010] border-[#75C900]'
                : isDeleted
                  ? 'bg-red-50 text-[#DC2626] border-red-200'
                  : 'bg-[#F5F5F5] text-[#101010] border-[#E5E5E5]';

              return (
                <li key={act.id} className="ml-5">
                  <span
                    className={`absolute -left-[7px] mt-1.5 w-3 h-3 rounded-full border-2 border-white ${
                      isCompleted
                        ? 'bg-[#75C900]'
                        : isDeleted
                          ? 'bg-[#DC2626]'
                          : 'bg-[#101010]'
                    }`}
                  />
                  <div className="p-3.5 rounded-xl border border-[#E5E5E5] bg-white hover:border-neutral-300 transition-colors">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge className={badgeStyle}>{actionLabel}</Badge>
                        <span className="text-xs font-semibold text-[#737373] uppercase">
                          {act.entity_type.replace('_', ' ')} #{act.entity_id}
                        </span>
                        {act.project_name && (
                          <span className="text-xs text-[#737373]">
                            · {act.project_name}
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-[#737373]">
                        {formatRelativeTime(act.created_at)} ({formatDateTime(act.created_at)})
                      </span>
                    </div>
                    <p className="text-sm font-medium text-[#101010] mt-2">
                      {act.description}
                    </p>
                    <p className="text-xs text-[#737373] mt-1">
                      Performed by <strong className="text-[#101010]">{act.user_name}</strong>
                    </p>
                  </div>
                </li>
              );
            })}
          </ol>
        </Card>
      )}
    </div>
  );
}
