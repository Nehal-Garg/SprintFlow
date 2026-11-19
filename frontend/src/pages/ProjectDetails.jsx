import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  Activity,
  ArrowLeft,
  Calendar,
  ChevronDown,
  ChevronRight,
  Clock,
  Edit3,
  Eye,
  Layers,
  Plus,
  Trash2,
  UserPlus,
  Users,
  X,
} from 'lucide-react';
import { projectsApi } from '../services/projects';
import { storiesApi } from '../services/stories';
import { tasksApi } from '../services/tasks';
import { authApi } from '../services/auth';
import { activityApi } from '../services/dashboard';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/common/Button';
import { ConfirmDialog } from '../components/common/Modal';
import {
  Card,
  EmptyState,
  ErrorBanner,
  LoadingSpinner,
  PriorityBadge,
  ProgressBar,
  StatusBadge,
} from '../components/common/UI';
import { ProjectModal } from '../components/projects/ProjectModal';
import { StoryModal } from '../components/stories/StoryModal';
import { TaskModal } from '../components/tasks/TaskModal';
import { TaskDetailModal } from '../components/tasks/TaskDetailModal';
import { PRIORITIES, STORY_STATUSES, TASK_STATUSES } from '../utils/constants';
import {
  extractErrorMessage,
  formatDate,
  formatRelativeTime,
  getInitials,
} from '../utils/formatters';

export function ProjectDetails() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { user, refreshUnreadCount } = useAuth();
  const toast = useToast();

  const [project, setProject] = useState(null);
  const [stories, setStories] = useState([]);
  const [tasksByStory, setTasksByStory] = useState({});
  const [expandedStories, setExpandedStories] = useState({});
  const [activities, setActivities] = useState([]);
  const [allUsers, setAllUsers] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Story filters
  const [storyPriorityFilter, setStoryPriorityFilter] = useState('');
  const [storyStatusFilter, setStoryStatusFilter] = useState('');

  // Member add state
  const [selectedUserId, setSelectedUserId] = useState('');
  const [selectedRole, setSelectedRole] = useState('member');
  const [addingMember, setAddingMember] = useState(false);

  // Modals
  const [projectModalOpen, setProjectModalOpen] = useState(false);
  const [confirmDeleteProject, setConfirmDeleteProject] = useState(false);
  const [storyModalState, setStoryModalState] = useState({ open: false, story: null });
  const [deletingStory, setDeletingStory] = useState(null);
  const [taskModalState, setTaskModalState] = useState({
    open: false,
    story: null,
    task: null,
  });
  const [deletingTask, setDeletingTask] = useState(null);
  const [viewingTask, setViewingTask] = useState(null);
  const [deleteBusy, setDeleteBusy] = useState(false);

  const loadTasksForStory = useCallback(async (storyId) => {
    const res = await tasksApi.listByStory(storyId, { limit: 200 });
    setTasksByStory((prev) => ({ ...prev, [storyId]: res.items || [] }));
  }, []);

  const loadWorkspace = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const storyParams = {};
      if (storyPriorityFilter) storyParams.priority = storyPriorityFilter;
      if (storyStatusFilter) storyParams.status = storyStatusFilter;

      const [projData, storiesData, actData, usersData] = await Promise.all([
        projectsApi.get(projectId),
        storiesApi.listByProject(projectId, storyParams),
        activityApi.list({ project_id: projectId, limit: 10 }),
        authApi.listUsers(),
      ]);

      setProject(projData);
      const storyList = storiesData.items || [];
      setStories(storyList);
      setActivities(actData.items || []);
      setAllUsers(usersData || []);

      // Auto-expand all stories on first load and fetch their tasks so the 3-level hierarchy is immediately visible
      const nextExpanded = {};
      const taskEntries = await Promise.all(
        storyList.map(async (s) => {
          nextExpanded[s.id] = true;
          const tRes = await tasksApi.listByStory(s.id, { limit: 200 });
          return [s.id, tRes.items || []];
        })
      );
      setExpandedStories((prev) =>
        Object.keys(prev).length > 0 ? { ...nextExpanded, ...prev } : nextExpanded
      );
      setTasksByStory(Object.fromEntries(taskEntries));
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to load project workspace.'));
    } finally {
      setLoading(false);
    }
  }, [projectId, storyPriorityFilter, storyStatusFilter]);

  useEffect(() => {
    loadWorkspace();
  }, [loadWorkspace]);

  const isOwner = project?.current_user_role === 'owner';

  const handleUpdateProject = async (payload) => {
    await projectsApi.update(projectId, payload);
    toast.success('Project updated.');
    await loadWorkspace();
  };

  const handleDeleteProject = async () => {
    setDeleteBusy(true);
    try {
      await projectsApi.remove(projectId);
      toast.success('Project deleted.');
      navigate('/projects', { replace: true });
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Failed to delete project.'));
    } finally {
      setDeleteBusy(false);
    }
  };

  const handleAddMember = async (e) => {
    e.preventDefault();
    if (!selectedUserId) return;
    setAddingMember(true);
    try {
      await projectsApi.addMember(projectId, {
        user_id: Number(selectedUserId),
        role: selectedRole,
      });
      toast.success('Team member added to project.');
      setSelectedUserId('');
      await loadWorkspace();
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Could not add member.'));
    } finally {
      setAddingMember(false);
    }
  };

  const handleRemoveMember = async (memberUserId, memberName) => {
    try {
      await projectsApi.removeMember(projectId, memberUserId);
      toast.success(`Removed ${memberName} from project.`);
      await loadWorkspace();
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Could not remove member.'));
    }
  };

  const handleSaveStory = async (payload) => {
    if (storyModalState.story) {
      await storiesApi.update(storyModalState.story.id, payload);
      toast.success('User story updated.');
    } else {
      await storiesApi.create(projectId, payload);
      toast.success('User story created.');
    }
    await loadWorkspace();
  };

  const handleDeleteStory = async () => {
    if (!deletingStory) return;
    setDeleteBusy(true);
    try {
      await storiesApi.remove(deletingStory.id);
      toast.success(`User story "${deletingStory.title}" deleted.`);
      setDeletingStory(null);
      await loadWorkspace();
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Could not delete user story.'));
    } finally {
      setDeleteBusy(false);
    }
  };

  const handleSaveTask = async (payload) => {
    if (taskModalState.task) {
      await tasksApi.update(taskModalState.task.id, payload);
      toast.success('Task updated.');
    } else if (taskModalState.story) {
      await tasksApi.create(taskModalState.story.id, payload);
      toast.success('Task created.');
    }
    await loadWorkspace();
    refreshUnreadCount();
  };

  const handleInlineTaskStatus = async (taskId, newStatus, storyId) => {
    try {
      const updated = await tasksApi.updateStatus(taskId, newStatus);
      toast.success(`Task moved to "${newStatus}".`);
      if (viewingTask?.id === taskId) setViewingTask(updated);
      await Promise.all([
        loadTasksForStory(storyId),
        projectsApi.get(projectId).then(setProject),
        activityApi.list({ project_id: projectId, limit: 10 }).then((r) => setActivities(r.items || [])),
      ]);
      refreshUnreadCount();
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Status update failed.'));
    }
  };

  const handleDeleteTask = async () => {
    if (!deletingTask) return;
    setDeleteBusy(true);
    try {
      await tasksApi.remove(deletingTask.id);
      toast.success(`Task "${deletingTask.title}" deleted.`);
      setDeletingTask(null);
      await loadWorkspace();
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Failed to delete task.'));
    } finally {
      setDeleteBusy(false);
    }
  };

  if (loading && !project) {
    return <LoadingSpinner label="Loading project workspace..." />;
  }

  if (error && !project) {
    return (
      <div className="space-y-4">
        <Link to="/projects" className="inline-flex items-center gap-1.5 text-sm font-semibold text-[#101010]">
          <ArrowLeft className="w-4 h-4" /> Back to Projects
        </Link>
        <ErrorBanner message={error} onRetry={loadWorkspace} />
      </div>
    );
  }

  const existingMemberIds = new Set((project?.members || []).map((m) => m.user_id));
  const availableUsersToAdd = allUsers.filter((u) => !existingMemberIds.has(u.id));

  return (
    <div className="space-y-6">
      {/* Breadcrumb & Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <Link
            to="/projects"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#737373] hover:text-[#101010] mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> All Projects
          </Link>
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="text-2xl font-bold text-[#101010]">{project.name}</h2>
            <StatusBadge status={project.status} />
            <span className="text-xs px-2 py-0.5 rounded bg-[#101010] text-[#75C900] font-semibold uppercase">
              {project.current_user_role}
            </span>
          </div>
          <p className="text-sm text-[#737373] mt-1 max-w-2xl">
            {project.description || 'No project description provided.'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={() => setProjectModalOpen(true)}>
            <Edit3 className="w-3.5 h-3.5" /> Edit
          </Button>
          {isOwner && (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setConfirmDeleteProject(true)}
            >
              <Trash2 className="w-3.5 h-3.5" /> Delete
            </Button>
          )}
        </div>
      </div>

      {/* Overview Bar */}
      <Card surface className="p-5 grid grid-cols-1 md:grid-cols-4 gap-5 items-center">
        <div className="md:col-span-2">
          <div className="flex items-center justify-between text-xs font-semibold text-[#101010] mb-1.5">
            <span>Overall Project Progress</span>
            <span>
              {project.completed_task_count} of {project.task_count} tasks completed
            </span>
          </div>
          <ProgressBar value={project.progress} height="h-2.5" />
        </div>
        <div className="text-xs space-y-1">
          <span className="text-[#737373] flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5" /> Schedule
          </span>
          <p className="font-semibold text-[#101010]">
            {formatDate(project.start_date)} → {formatDate(project.end_date)}
          </p>
        </div>
        <div className="text-xs space-y-1">
          <span className="text-[#737373] flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5" /> Work Breakdown
          </span>
          <p className="font-semibold text-[#101010]">
            {project.story_count} User Stories · {project.task_count} Tasks
          </p>
        </div>
      </Card>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 items-start">
        {/* Left 2 columns: User Stories -> Tasks hierarchy */}
        <div className="xl:col-span-2 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-bold text-[#101010]">
                User Stories & Tasks
              </h3>
              <p className="text-xs text-[#737373]">
                Project → User Story → Task hierarchy
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={storyPriorityFilter}
                onChange={(e) => setStoryPriorityFilter(e.target.value)}
                className="rounded-lg border border-[#E5E5E5] bg-white px-2.5 py-1.5 text-xs text-[#101010]"
              >
                <option value="">All Priorities</option>
                {PRIORITIES.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
              <select
                value={storyStatusFilter}
                onChange={(e) => setStoryStatusFilter(e.target.value)}
                className="rounded-lg border border-[#E5E5E5] bg-white px-2.5 py-1.5 text-xs text-[#101010]"
              >
                <option value="">All Statuses</option>
                {STORY_STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
              <Button
                size="sm"
                onClick={() => setStoryModalState({ open: true, story: null })}
              >
                <Plus className="w-3.5 h-3.5" /> Add User Story
              </Button>
            </div>
          </div>

          {stories.length === 0 ? (
            <EmptyState
              icon={Layers}
              title="No user stories in this project"
              description="Create a user story to break this project into actionable Agile tasks."
              action={
                <Button
                  size="sm"
                  onClick={() => setStoryModalState({ open: true, story: null })}
                >
                  <Plus className="w-4 h-4" /> Create First User Story
                </Button>
              }
            />
          ) : (
            <div className="space-y-4">
              {stories.map((story) => {
                const isExpanded = Boolean(expandedStories[story.id]);
                const storyTasks = tasksByStory[story.id] || [];

                return (
                  <Card key={story.id} className="overflow-hidden">
                    {/* Story Header */}
                    <div className="p-4 sm:p-5 bg-[#F5F5F5]/70 border-b border-[#E5E5E5]">
                      <div className="flex items-start justify-between gap-3">
                        <button
                          type="button"
                          onClick={() =>
                            setExpandedStories((prev) => ({
                              ...prev,
                              [story.id]: !prev[story.id],
                            }))
                          }
                          className="flex items-start gap-2.5 text-left flex-1 min-w-0"
                        >
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4 text-[#101010] mt-1 shrink-0" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-[#101010] mt-1 shrink-0" />
                          )}
                          <div className="min-w-0">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="text-sm font-bold text-[#101010]">
                                {story.title}
                              </span>
                              <StatusBadge status={story.status} />
                              <PriorityBadge priority={story.priority} />
                              {story.story_points !== null &&
                                story.story_points !== undefined && (
                                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-white border border-[#E5E5E5] text-[#101010]">
                                    {story.story_points} pts
                                  </span>
                                )}
                            </div>
                            {story.description && (
                              <p className="text-xs text-[#737373] mt-1">
                                {story.description}
                              </p>
                            )}
                            {story.acceptance_criteria && (
                              <p className="text-[11px] text-[#101010] mt-1.5 bg-white border border-[#E5E5E5] rounded px-2.5 py-1.5">
                                <span className="font-semibold">Acceptance Criteria:</span>{' '}
                                {story.acceptance_criteria}
                              </p>
                            )}
                            <div className="flex flex-wrap items-center gap-3 text-[11px] text-[#737373] mt-2">
                              <span>
                                Owner: <strong className="text-[#101010]">{story.assignee_name || 'Unassigned'}</strong>
                              </span>
                              <span>Due: {formatDate(story.due_date)}</span>
                              <span>
                                Tasks: {story.completed_task_count}/{story.task_count} done
                              </span>
                            </div>
                          </div>
                        </button>

                        <div className="flex items-center gap-1 shrink-0">
                          <Button
                            size="sm"
                            variant="primary"
                            onClick={() =>
                              setTaskModalState({ open: true, story, task: null })
                            }
                          >
                            <Plus className="w-3.5 h-3.5" /> Task
                          </Button>
                          <button
                            type="button"
                            onClick={() =>
                              setStoryModalState({ open: true, story })
                            }
                            className="p-1.5 rounded-lg text-[#737373] hover:text-[#101010] hover:bg-white"
                            title="Edit user story"
                          >
                            <Edit3 className="w-4 h-4" />
                          </button>
                          <button
                            type="button"
                            onClick={() => setDeletingStory(story)}
                            className="p-1.5 rounded-lg text-[#737373] hover:text-[#DC2626] hover:bg-red-50"
                            title="Delete user story"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Nested Tasks */}
                    {isExpanded && (
                      <div className="p-4 bg-white">
                        {storyTasks.length === 0 ? (
                          <div className="text-center py-6 text-xs text-[#737373]">
                            No tasks under this user story yet.{' '}
                            <button
                              type="button"
                              onClick={() =>
                                setTaskModalState({ open: true, story, task: null })
                              }
                              className="font-semibold text-[#101010] underline decoration-[#75C900] decoration-2"
                            >
                              Add the first task
                            </button>
                          </div>
                        ) : (
                          <div className="divide-y divide-[#E5E5E5]">
                            {storyTasks.map((task) => (
                              <div
                                key={task.id}
                                className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                              >
                                <div className="min-w-0 flex-1">
                                  <div className="flex flex-wrap items-center gap-2">
                                    <button
                                      type="button"
                                      onClick={() => setViewingTask(task)}
                                      className="text-sm font-semibold text-[#101010] hover:text-[#66B000] text-left"
                                    >
                                      {task.title}
                                    </button>
                                    <PriorityBadge priority={task.priority} />
                                    {task.is_overdue && (
                                      <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded bg-red-50 text-[#DC2626] border border-red-200">
                                        Overdue
                                      </span>
                                    )}
                                  </div>
                                  <div className="flex flex-wrap items-center gap-3 text-[11px] text-[#737373] mt-1">
                                    <span>Assignee: {task.assignee_name || 'Unassigned'}</span>
                                    <span className={task.is_overdue ? 'text-[#DC2626] font-semibold' : ''}>
                                      Due: {formatDate(task.due_date)}
                                    </span>
                                    {(task.estimated_hours || task.actual_hours) && (
                                      <span className="inline-flex items-center gap-1">
                                        <Clock className="w-3 h-3" />
                                        {task.actual_hours ?? 0}h / {task.estimated_hours ?? 0}h
                                      </span>
                                    )}
                                  </div>
                                </div>

                                <div className="flex items-center gap-2 shrink-0">
                                  <select
                                    value={task.status}
                                    onChange={(e) =>
                                      handleInlineTaskStatus(task.id, e.target.value, story.id)
                                    }
                                    className="rounded-lg border border-[#E5E5E5] bg-[#F5F5F5] px-2.5 py-1 text-xs font-semibold text-[#101010] focus:outline-none focus:ring-2 focus:ring-[#75C900]"
                                    aria-label={`Change status for ${task.title}`}
                                  >
                                    {TASK_STATUSES.map((st) => (
                                      <option key={st} value={st}>
                                        {st}
                                      </option>
                                    ))}
                                  </select>
                                  <button
                                    type="button"
                                    onClick={() => setViewingTask(task)}
                                    className="p-1.5 rounded-lg text-[#737373] hover:text-[#101010] hover:bg-[#F5F5F5]"
                                    title="View task details"
                                  >
                                    <Eye className="w-4 h-4" />
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() =>
                                      setTaskModalState({ open: true, story, task })
                                    }
                                    className="p-1.5 rounded-lg text-[#737373] hover:text-[#101010] hover:bg-[#F5F5F5]"
                                    title="Edit task"
                                  >
                                    <Edit3 className="w-4 h-4" />
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => setDeletingTask(task)}
                                    className="p-1.5 rounded-lg text-[#737373] hover:text-[#DC2626] hover:bg-red-50"
                                    title="Delete task"
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </button>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </Card>
                );
              })}
            </div>
          )}
        </div>

        {/* Right column: Team Members & Recent Project Activity */}
        <div className="space-y-5">
          {/* Members Card */}
          <Card className="p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-[#101010] flex items-center gap-2">
                <Users className="w-4 h-4 text-[#75C900]" />
                Project Team ({project.members.length})
              </h3>
            </div>

            <div className="space-y-2.5">
              {project.members.map((m) => (
                <div
                  key={m.id}
                  className="flex items-center justify-between gap-2 p-2.5 rounded-lg bg-[#F5F5F5] border border-[#E5E5E5]"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className="w-7 h-7 rounded-full bg-[#101010] text-[#75C900] text-[11px] font-bold flex items-center justify-center shrink-0">
                      {getInitials(m.full_name)}
                    </span>
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-[#101010] truncate">
                        {m.full_name} {m.user_id === user?.id && '(You)'}
                      </p>
                      <p className="text-[11px] text-[#737373] truncate">{m.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <span
                      className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${
                        m.role === 'owner'
                          ? 'bg-[#101010] text-[#75C900]'
                          : 'bg-white border border-[#E5E5E5] text-[#737373]'
                      }`}
                    >
                      {m.role}
                    </span>
                    {isOwner && m.user_id !== user?.id && (
                      <button
                        type="button"
                        onClick={() => handleRemoveMember(m.user_id, m.full_name)}
                        className="p-1 rounded text-[#737373] hover:text-[#DC2626] hover:bg-red-50"
                        title="Remove member"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {isOwner && (
              <form onSubmit={handleAddMember} className="mt-4 pt-4 border-t border-[#E5E5E5] space-y-2.5">
                <label className="text-xs font-semibold text-[#101010] flex items-center gap-1.5">
                  <UserPlus className="w-3.5 h-3.5" /> Add Team Member
                </label>
                {availableUsersToAdd.length === 0 ? (
                  <p className="text-xs text-[#737373]">
                    All registered team users are already members of this project.
                  </p>
                ) : (
                  <>
                    <div className="flex gap-2">
                      <select
                        value={selectedUserId}
                        onChange={(e) => setSelectedUserId(e.target.value)}
                        className="flex-1 rounded-lg border border-[#E5E5E5] bg-white px-2.5 py-1.5 text-xs text-[#101010]"
                        required
                      >
                        <option value="">Select user...</option>
                        {availableUsersToAdd.map((u) => (
                          <option key={u.id} value={u.id}>
                            {u.full_name} ({u.email})
                          </option>
                        ))}
                      </select>
                      <select
                        value={selectedRole}
                        onChange={(e) => setSelectedRole(e.target.value)}
                        className="rounded-lg border border-[#E5E5E5] bg-white px-2 py-1.5 text-xs text-[#101010]"
                      >
                        <option value="member">Member</option>
                        <option value="owner">Owner</option>
                      </select>
                    </div>
                    <Button
                      type="submit"
                      size="sm"
                      className="w-full"
                      loading={addingMember}
                      disabled={!selectedUserId}
                    >
                      Add to Project
                    </Button>
                  </>
                )}
              </form>
            )}
          </Card>

          {/* Recent Project Activity */}
          <Card className="p-5">
            <h3 className="text-sm font-bold text-[#101010] flex items-center gap-2 mb-4">
              <Activity className="w-4 h-4 text-[#75C900]" />
              Recent Project Activity
            </h3>
            {activities.length === 0 ? (
              <p className="text-xs text-[#737373]">No activity recorded yet.</p>
            ) : (
              <div className="space-y-3">
                {activities.map((act) => (
                  <div key={act.id} className="flex items-start gap-2.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#75C900] mt-1.5 shrink-0" />
                    <div className="min-w-0">
                      <p className="text-xs text-[#101010] leading-snug">{act.description}</p>
                      <p className="text-[11px] text-[#737373] mt-0.5">
                        {act.user_name} · {formatRelativeTime(act.created_at)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Modals */}
      <ProjectModal
        open={projectModalOpen}
        onClose={() => setProjectModalOpen(false)}
        initialData={project}
        onSubmit={handleUpdateProject}
      />

      <StoryModal
        open={storyModalState.open}
        onClose={() => setStoryModalState({ open: false, story: null })}
        initialData={storyModalState.story}
        members={project.members}
        onSubmit={handleSaveStory}
      />

      <TaskModal
        open={taskModalState.open}
        onClose={() => setTaskModalState({ open: false, story: null, task: null })}
        initialData={taskModalState.task}
        storyTitle={taskModalState.story?.title}
        members={project.members}
        onSubmit={handleSaveTask}
      />

      <TaskDetailModal
        open={Boolean(viewingTask)}
        task={viewingTask}
        onClose={() => setViewingTask(null)}
        onStatusChange={(tid, st) =>
          handleInlineTaskStatus(tid, st, viewingTask.user_story_id)
        }
      />

      <ConfirmDialog
        open={confirmDeleteProject}
        onClose={() => setConfirmDeleteProject(false)}
        onConfirm={handleDeleteProject}
        loading={deleteBusy}
        title="Delete Project?"
        message={`Deleting "${project.name}" will cascade-delete all user stories and tasks inside it.`}
        confirmLabel="Delete Project"
      />

      <ConfirmDialog
        open={Boolean(deletingStory)}
        onClose={() => setDeletingStory(null)}
        onConfirm={handleDeleteStory}
        loading={deleteBusy}
        title="Delete User Story?"
        message={`Deleting "${deletingStory?.title}" will permanently remove the story and all tasks under it.`}
        confirmLabel="Delete Story"
      />

      <ConfirmDialog
        open={Boolean(deletingTask)}
        onClose={() => setDeletingTask(null)}
        onConfirm={handleDeleteTask}
        loading={deleteBusy}
        title="Delete Task?"
        message={`Are you sure you want to delete task "${deletingTask?.title}"?`}
        confirmLabel="Delete Task"
      />
    </div>
  );
}
