import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowUpRight,
  CalendarClock,
  CheckCircle2,
  ClipboardList,
  FolderKanban,
  Layers,
  RefreshCw,
  Rocket,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { dashboardApi } from '../services/dashboard';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';
import {
  Card,
  EmptyState,
  ErrorBanner,
  LoadingSpinner,
  PriorityBadge,
  ProgressBar,
  StatusBadge,
} from '../components/common/UI';
import { extractErrorMessage, formatDate, formatRelativeTime } from '../utils/formatters';

const STATUS_CHART_COLORS = ['#737373', '#101010', '#F59E0B', '#75C900'];
const PRIORITY_CHART_COLORS = ['#A3A3A3', '#101010', '#F59E0B', '#DC2626'];
const COMPLETION_COLORS = ['#75C900', '#101010'];

export function Dashboard() {
  const { user, refreshUnreadCount } = useAuth();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await dashboardApi.getSummary();
      setSummary(data);
      refreshUnreadCount();
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to load dashboard metrics.'));
    } finally {
      setLoading(false);
    }
  }, [refreshUnreadCount]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  if (loading && !summary) {
    return <LoadingSpinner label="Loading live dashboard analytics..." />;
  }

  const kpis = summary
    ? [
        { label: 'Total Projects', value: summary.total_projects, icon: FolderKanban, accent: 'text-[#101010]' },
        { label: 'Active Projects', value: summary.active_projects, icon: Rocket, accent: 'text-[#75C900]' },
        { label: 'Completed Projects', value: summary.completed_projects, icon: CheckCircle2, accent: 'text-[#16A34A]' },
        { label: 'User Stories', value: summary.total_stories, icon: Layers, accent: 'text-[#101010]' },
        { label: 'Total Tasks', value: summary.total_tasks, icon: ClipboardList, accent: 'text-[#101010]' },
        { label: 'Completed Tasks', value: summary.completed_tasks, icon: CheckCircle2, accent: 'text-[#16A34A]' },
        {
          label: 'Overdue Tasks',
          value: summary.overdue_tasks,
          icon: AlertTriangle,
          accent: summary.overdue_tasks > 0 ? 'text-[#DC2626]' : 'text-[#737373]',
        },
      ]
    : [];

  const completedVsPending = summary
    ? [
        { name: 'Completed', value: summary.completed_tasks },
        { name: 'Pending', value: summary.pending_tasks },
      ]
    : [];

  const hasTasks = (summary?.total_tasks || 0) > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#101010]">
            Welcome back, {user?.full_name?.split(' ')[0]}
          </h2>
          <p className="text-sm text-[#737373]">
            Live metrics calculated directly from your projects, stories, and tasks.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Button variant="secondary" size="sm" onClick={loadDashboard} loading={loading}>
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </Button>
          <Link to="/projects">
            <Button size="sm">Manage Projects</Button>
          </Link>
        </div>
      </div>

      <ErrorBanner message={error} onRetry={loadDashboard} />

      {summary && (
        <>
          {/* 7 KPI Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 xl:grid-cols-7 gap-3.5">
            {kpis.map(({ label, value, icon: Icon, accent }) => (
              <Card key={label} surface className="p-4 flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold uppercase tracking-wide text-[#737373]">
                    {label}
                  </span>
                  <Icon className={`w-4 h-4 ${accent}`} />
                </div>
                <p className="text-2xl font-bold text-[#101010] mt-2 tabular-nums">
                  {value}
                </p>
              </Card>
            ))}
          </div>

          {/* 4 Recharts Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* 1. Tasks by Status */}
            <Card className="p-5">
              <div className="mb-4">
                <h3 className="text-sm font-bold text-[#101010]">Tasks by Status</h3>
                <p className="text-xs text-[#737373]">Workflow distribution across Kanban stages</p>
              </div>
              {hasTasks ? (
                <div className="h-60">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={summary.tasks_by_status} margin={{ top: 5, right: 16, left: -16, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E5" />
                      <XAxis dataKey="status" tick={{ fontSize: 12, fill: '#101010' }} />
                      <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: '#737373' }} />
                      <Tooltip />
                      <Bar dataKey="count" name="Tasks" radius={[6, 6, 0, 0]}>
                        {summary.tasks_by_status.map((_, idx) => (
                          <Cell key={idx} fill={STATUS_CHART_COLORS[idx % STATUS_CHART_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <EmptyState title="No tasks yet" description="Create tasks inside a project user story to populate status analytics." />
              )}
            </Card>

            {/* 2. Project Progress */}
            <Card className="p-5">
              <div className="mb-4">
                <h3 className="text-sm font-bold text-[#101010]">Project Progress (%)</h3>
                <p className="text-xs text-[#737373]">Completion percentage based on Done tasks</p>
              </div>
              {summary.project_progress.length > 0 ? (
                <div className="h-60">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={summary.project_progress}
                      layout="vertical"
                      margin={{ top: 5, right: 24, left: 10, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E5" />
                      <XAxis type="number" domain={[0, 100]} unit="%" tick={{ fontSize: 11, fill: '#737373' }} />
                      <YAxis
                        type="category"
                        dataKey="project_name"
                        width={110}
                        tick={{ fontSize: 11, fill: '#101010' }}
                      />
                      <Tooltip formatter={(val) => [`${val}%`, 'Progress']} />
                      <Bar dataKey="progress" fill="#75C900" radius={[0, 6, 6, 0]} barSize={20} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <EmptyState title="No projects yet" description="Create your first project to monitor delivery progress." />
              )}
            </Card>

            {/* 3. Completed vs Pending */}
            <Card className="p-5">
              <div className="mb-4">
                <h3 className="text-sm font-bold text-[#101010]">Completed vs Pending Tasks</h3>
                <p className="text-xs text-[#737373]">Overall delivery completion ratio</p>
              </div>
              {hasTasks ? (
                <div className="h-60">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={completedVsPending}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        innerRadius={55}
                        outerRadius={85}
                        paddingAngle={3}
                      >
                        {completedVsPending.map((_, idx) => (
                          <Cell key={idx} fill={COMPLETION_COLORS[idx]} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <EmptyState title="No completion data" description="Task completion metrics appear once tasks are added." />
              )}
            </Card>

            {/* 4. Task Priority Distribution */}
            <Card className="p-5">
              <div className="mb-4">
                <h3 className="text-sm font-bold text-[#101010]">Task Priority Distribution</h3>
                <p className="text-xs text-[#737373]">Workload split by urgency level</p>
              </div>
              {hasTasks ? (
                <div className="h-60">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={summary.tasks_by_priority} margin={{ top: 5, right: 16, left: -16, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E5" />
                      <XAxis dataKey="priority" tick={{ fontSize: 12, fill: '#101010' }} />
                      <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: '#737373' }} />
                      <Tooltip />
                      <Bar dataKey="count" name="Tasks" radius={[6, 6, 0, 0]}>
                        {summary.tasks_by_priority.map((_, idx) => (
                          <Cell key={idx} fill={PRIORITY_CHART_COLORS[idx % PRIORITY_CHART_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <EmptyState title="No priority breakdown" description="Create tasks with priorities to view distribution." />
              )}
            </Card>
          </div>

          {/* Additional 6 Live Sections */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Recent Projects */}
            <Card className="p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-[#101010]">Recent Projects</h3>
                <Link to="/projects" className="text-xs font-semibold text-[#101010] hover:text-[#66B000] inline-flex items-center gap-1">
                  View all <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
              </div>
              {summary.recent_projects.length > 0 ? (
                <div className="space-y-3">
                  {summary.recent_projects.map((p) => (
                    <Link
                      key={p.id}
                      to={`/projects/${p.id}`}
                      className="block p-3.5 rounded-xl border border-[#E5E5E5] bg-[#F5F5F5]/60 hover:border-[#101010] transition-colors"
                    >
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <span className="text-sm font-semibold text-[#101010] truncate">{p.name}</span>
                        <StatusBadge status={p.status} />
                      </div>
                      <ProgressBar value={p.progress} />
                      <div className="flex items-center justify-between text-[11px] text-[#737373] mt-2">
                        <span>{p.story_count} stories · {p.completed_task_count}/{p.task_count} tasks</span>
                        <span>Due: {formatDate(p.end_date)}</span>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <EmptyState title="No projects yet" description="Start by creating a project in the Projects tab." />
              )}
            </Card>

            {/* My Assigned Tasks */}
            <Card className="p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-[#101010]">My Assigned Tasks</h3>
                <Link to="/my-tasks" className="text-xs font-semibold text-[#101010] hover:text-[#66B000] inline-flex items-center gap-1">
                  Open My Tasks <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
              </div>
              {summary.my_assigned_tasks.length > 0 ? (
                <div className="divide-y divide-[#E5E5E5]">
                  {summary.my_assigned_tasks.map((t) => (
                    <div key={t.id} className="py-2.5 flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-[#101010] truncate">{t.title}</p>
                        <p className="text-xs text-[#737373] truncate">
                          {t.project_name} · {t.user_story_title}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <StatusBadge status={t.status} />
                        <span className={`text-xs font-medium ${t.is_overdue ? 'text-[#DC2626]' : 'text-[#737373]'}`}>
                          {formatDate(t.due_date)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="No tasks assigned to you" description="Tasks assigned to you will appear here." />
              )}
            </Card>

            {/* Upcoming Deadlines */}
            <Card className="p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-[#101010] flex items-center gap-2">
                  <CalendarClock className="w-4 h-4 text-[#F59E0B]" />
                  Upcoming Deadlines (Next 7 Days)
                </h3>
              </div>
              {summary.upcoming_deadlines.length > 0 ? (
                <div className="divide-y divide-[#E5E5E5]">
                  {summary.upcoming_deadlines.map((t) => (
                    <div key={t.id} className="py-2.5 flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-[#101010] truncate">{t.title}</p>
                        <p className="text-xs text-[#737373] truncate">
                          {t.project_name} · {t.assignee_name || 'Unassigned'}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <PriorityBadge priority={t.priority} />
                        <span className="text-xs font-semibold text-amber-700">{formatDate(t.due_date)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="No upcoming deadlines" description="No open tasks are due within the next 7 days." />
              )}
            </Card>

            {/* Overdue Tasks */}
            <Card className="p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-[#101010] flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-[#DC2626]" />
                  Overdue Tasks
                </h3>
              </div>
              {summary.overdue_task_list.length > 0 ? (
                <div className="divide-y divide-[#E5E5E5]">
                  {summary.overdue_task_list.map((t) => (
                    <div key={t.id} className="py-2.5 flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-[#101010] truncate">{t.title}</p>
                        <p className="text-xs text-[#737373] truncate">
                          {t.project_name} · {t.assignee_name || 'Unassigned'}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <StatusBadge status={t.status} />
                        <span className="text-xs font-semibold text-[#DC2626]">{formatDate(t.due_date)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="All on track" description="Zero overdue tasks across your accessible projects." />
              )}
            </Card>

            {/* Recently Updated Tasks */}
            <Card className="p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-[#101010]">Recently Updated Tasks</h3>
                <Link to="/kanban" className="text-xs font-semibold text-[#101010] hover:text-[#66B000] inline-flex items-center gap-1">
                  Kanban Board <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
              </div>
              {summary.recently_updated_tasks.length > 0 ? (
                <div className="divide-y divide-[#E5E5E5]">
                  {summary.recently_updated_tasks.map((t) => (
                    <div key={t.id} className="py-2.5 flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-[#101010] truncate">{t.title}</p>
                        <p className="text-xs text-[#737373] truncate">
                          {t.project_name} · Updated {formatRelativeTime(t.updated_at)}
                        </p>
                      </div>
                      <StatusBadge status={t.status} />
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="No recent task updates" description="Updates to tasks will appear here automatically." />
              )}
            </Card>

            {/* Recent Activity */}
            <Card className="p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-[#101010]">Recent Activity</h3>
                <Link to="/activity" className="text-xs font-semibold text-[#101010] hover:text-[#66B000] inline-flex items-center gap-1">
                  Full log <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
              </div>
              {summary.recent_activity.length > 0 ? (
                <div className="space-y-3">
                  {summary.recent_activity.slice(0, 6).map((act) => (
                    <div key={act.id} className="flex items-start gap-3">
                      <span className="w-2 h-2 rounded-full bg-[#75C900] mt-1.5 shrink-0" />
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-medium text-[#101010]">{act.description}</p>
                        <p className="text-[11px] text-[#737373]">
                          {act.user_name} · {formatRelativeTime(act.created_at)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="No recent activity" description="Project, story, and task events will appear chronologically." />
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
