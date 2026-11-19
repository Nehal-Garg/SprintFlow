import { useCallback, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Calendar,
  Edit3,
  FolderKanban,
  Layers,
  Plus,
  Search,
  Trash2,
  Users,
} from 'lucide-react';
import { projectsApi } from '../services/projects';
import { useToast } from '../context/ToastContext';
import { useDebounce } from '../hooks/useDebounce';
import { Button } from '../components/common/Button';
import { ConfirmDialog } from '../components/common/Modal';
import {
  Card,
  EmptyState,
  ErrorBanner,
  LoadingSpinner,
  ProgressBar,
  StatusBadge,
} from '../components/common/UI';
import { ProjectModal } from '../components/projects/ProjectModal';
import { PROJECT_STATUSES } from '../utils/constants';
import { extractErrorMessage, formatDate } from '../utils/formatters';

export function Projects() {
  const [searchParams, setSearchParams] = useSearchParams();
  const toast = useToast();

  const [projects, setProjects] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [statusFilter, setStatusFilter] = useState(searchParams.get('status') || '');
  const debouncedSearch = useDebounce(search, 250);

  const [modalOpen, setModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [deletingProject, setDeletingProject] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  useEffect(() => {
    const urlSearch = searchParams.get('search') || '';
    if (urlSearch !== search) setSearch(urlSearch);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const loadProjects = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = {};
      if (debouncedSearch.trim()) params.search = debouncedSearch.trim();
      if (statusFilter) params.status = statusFilter;
      const data = await projectsApi.list(params);
      setProjects(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to load projects.'));
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, statusFilter]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const handleCreateOrUpdate = async (payload) => {
    if (editingProject) {
      await projectsApi.update(editingProject.id, payload);
      toast.success('Project updated successfully.');
    } else {
      await projectsApi.create(payload);
      toast.success('Project created successfully.');
    }
    await loadProjects();
  };

  const handleConfirmDelete = async () => {
    if (!deletingProject) return;
    setDeleteLoading(true);
    try {
      await projectsApi.remove(deletingProject.id);
      toast.success(`Project "${deletingProject.name}" deleted.`);
      setDeletingProject(null);
      await loadProjects();
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Unable to delete project.'));
    } finally {
      setDeleteLoading(false);
    }
  };

  const updateSearchInput = (val) => {
    setSearch(val);
    const next = new URLSearchParams(searchParams);
    if (val.trim()) next.set('search', val);
    else next.delete('search');
    setSearchParams(next, { replace: true });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#101010]">Projects</h2>
          <p className="text-sm text-[#737373]">
            {total} accessible {total === 1 ? 'project' : 'projects'} · Organize user stories and tasks hierarchically
          </p>
        </div>
        <Button
          onClick={() => {
            setEditingProject(null);
            setModalOpen(true);
          }}
        >
          <Plus className="w-4 h-4" />
          New Project
        </Button>
      </div>

      {/* Filters */}
      <Card surface className="p-4 flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-[#737373] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => updateSearchInput(e.target.value)}
            placeholder="Search projects by name or description..."
            className="w-full rounded-lg border border-[#E5E5E5] bg-white pl-9 pr-3 py-2 text-sm text-[#101010] placeholder:text-[#737373] focus:outline-none focus:ring-2 focus:ring-[#75C900] focus:border-[#101010]"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-[#E5E5E5] bg-white px-3 py-2 text-sm text-[#101010] focus:outline-none focus:ring-2 focus:ring-[#75C900]"
        >
          <option value="">All Statuses</option>
          {PROJECT_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        {(search || statusFilter) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              updateSearchInput('');
              setStatusFilter('');
            }}
          >
            Clear
          </Button>
        )}
      </Card>

      <ErrorBanner message={error} onRetry={loadProjects} />

      {loading ? (
        <LoadingSpinner label="Loading projects..." />
      ) : projects.length === 0 ? (
        <EmptyState
          icon={FolderKanban}
          title={search || statusFilter ? 'No matching projects' : 'No projects yet'}
          description={
            search || statusFilter
              ? 'Try adjusting your search query or status filter.'
              : 'Create your first Agile project to start adding user stories and tasks.'
          }
          action={
            !search && !statusFilter && (
              <Button
                onClick={() => {
                  setEditingProject(null);
                  setModalOpen(true);
                }}
              >
                <Plus className="w-4 h-4" />
                Create First Project
              </Button>
            )
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {projects.map((project) => (
            <Card
              key={project.id}
              className="p-5 flex flex-col justify-between hover:border-[#101010] transition-colors"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <Link
                    to={`/projects/${project.id}`}
                    className="text-base font-bold text-[#101010] hover:text-[#66B000] transition-colors line-clamp-1"
                  >
                    {project.name}
                  </Link>
                  <StatusBadge status={project.status} />
                </div>

                <p className="text-xs text-[#737373] mt-2 line-clamp-2 min-h-[32px]">
                  {project.description || 'No description provided.'}
                </p>

                <div className="mt-4">
                  <div className="flex items-center justify-between text-[11px] font-medium text-[#737373] mb-1.5">
                    <span>Completion Progress</span>
                    <span>
                      {project.completed_task_count}/{project.task_count} tasks done
                    </span>
                  </div>
                  <ProgressBar value={project.progress} />
                </div>

                <div className="grid grid-cols-2 gap-2.5 mt-4 pt-4 border-t border-[#E5E5E5] text-xs text-[#737373]">
                  <div className="flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-[#101010]" />
                    <span>{project.story_count} stories</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Users className="w-3.5 h-3.5 text-[#101010]" />
                    <span>{project.members.length} members</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-[#101010]" />
                    <span>Start: {formatDate(project.start_date)}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-[#75C900]" />
                    <span>Due: {formatDate(project.end_date)}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between gap-2 mt-5 pt-3.5 border-t border-[#E5E5E5]">
                <Link to={`/projects/${project.id}`}>
                  <Button variant="secondary" size="sm">
                    Open Workspace
                  </Button>
                </Link>
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => {
                      setEditingProject(project);
                      setModalOpen(true);
                    }}
                    className="p-2 rounded-lg text-[#737373] hover:text-[#101010] hover:bg-[#F5F5F5]"
                    title="Edit project"
                  >
                    <Edit3 className="w-4 h-4" />
                  </button>
                  {project.current_user_role === 'owner' && (
                    <button
                      type="button"
                      onClick={() => setDeletingProject(project)}
                      className="p-2 rounded-lg text-[#737373] hover:text-[#DC2626] hover:bg-red-50"
                      title="Delete project (owner only)"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <ProjectModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        initialData={editingProject}
        onSubmit={handleCreateOrUpdate}
      />

      <ConfirmDialog
        open={Boolean(deletingProject)}
        onClose={() => setDeletingProject(null)}
        onConfirm={handleConfirmDelete}
        loading={deleteLoading}
        title="Delete Project?"
        message={`Deleting "${deletingProject?.name}" will permanently remove the project along with all of its user stories and tasks. This action cannot be undone.`}
        confirmLabel="Delete Project"
      />
    </div>
  );
}
