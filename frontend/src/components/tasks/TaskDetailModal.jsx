import { Calendar, Clock, FolderKanban, Layers, User } from 'lucide-react';
import { Modal } from '../common/Modal';
import { PriorityBadge, StatusBadge } from '../common/UI';
import { TASK_STATUSES } from '../../utils/constants';
import { formatDate, formatDateTime } from '../../utils/formatters';

export function TaskDetailModal({ task, open, onClose, onStatusChange }) {
  if (!task) return null;

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={task.title}
      subtitle={`${task.project_name || 'Project'} → ${task.user_story_title || 'User Story'}`}
      maxWidth="max-w-lg"
    >
      <div className="space-y-5">
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge status={task.status} />
          <PriorityBadge priority={task.priority} />
          {task.is_overdue && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-50 text-[#DC2626] border border-red-300">
              Overdue
            </span>
          )}
        </div>

        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-[#737373] mb-1">
            Description
          </h4>
          <p className="text-sm text-[#101010] whitespace-pre-wrap bg-[#F5F5F5] rounded-lg p-3 border border-[#E5E5E5]">
            {task.description || 'No description provided.'}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded-lg border border-[#E5E5E5] bg-white">
            <div className="flex items-center gap-1.5 text-[#737373] mb-1">
              <FolderKanban className="w-3.5 h-3.5" />
              <span>Project</span>
            </div>
            <p className="font-semibold text-[#101010]">{task.project_name || '—'}</p>
          </div>
          <div className="p-3 rounded-lg border border-[#E5E5E5] bg-white">
            <div className="flex items-center gap-1.5 text-[#737373] mb-1">
              <Layers className="w-3.5 h-3.5" />
              <span>User Story</span>
            </div>
            <p className="font-semibold text-[#101010]">{task.user_story_title || '—'}</p>
          </div>
          <div className="p-3 rounded-lg border border-[#E5E5E5] bg-white">
            <div className="flex items-center gap-1.5 text-[#737373] mb-1">
              <User className="w-3.5 h-3.5" />
              <span>Assignee</span>
            </div>
            <p className="font-semibold text-[#101010]">{task.assignee_name || 'Unassigned'}</p>
          </div>
          <div className="p-3 rounded-lg border border-[#E5E5E5] bg-white">
            <div className="flex items-center gap-1.5 text-[#737373] mb-1">
              <Calendar className="w-3.5 h-3.5" />
              <span>Due Date</span>
            </div>
            <p className={`font-semibold ${task.is_overdue ? 'text-[#DC2626]' : 'text-[#101010]'}`}>
              {formatDate(task.due_date)}
            </p>
          </div>
          <div className="p-3 rounded-lg border border-[#E5E5E5] bg-white">
            <div className="flex items-center gap-1.5 text-[#737373] mb-1">
              <Clock className="w-3.5 h-3.5" />
              <span>Estimated Hours</span>
            </div>
            <p className="font-semibold text-[#101010]">
              {task.estimated_hours !== null && task.estimated_hours !== undefined
                ? `${task.estimated_hours}h`
                : '—'}
            </p>
          </div>
          <div className="p-3 rounded-lg border border-[#E5E5E5] bg-white">
            <div className="flex items-center gap-1.5 text-[#737373] mb-1">
              <Clock className="w-3.5 h-3.5" />
              <span>Actual Hours</span>
            </div>
            <p className="font-semibold text-[#101010]">
              {task.actual_hours !== null && task.actual_hours !== undefined
                ? `${task.actual_hours}h`
                : '—'}
            </p>
          </div>
        </div>

        {onStatusChange && (
          <div className="pt-3 border-t border-[#E5E5E5]">
            <label className="block text-xs font-semibold text-[#101010] mb-1.5">
              Quick Status Update
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {TASK_STATUSES.map((st) => (
                <button
                  key={st}
                  type="button"
                  onClick={() => onStatusChange(task.id, st)}
                  className={`px-2.5 py-2 rounded-lg text-xs font-semibold border transition-colors ${
                    task.status === st
                      ? 'bg-[#75C900] text-[#101010] border-[#75C900]'
                      : 'bg-white text-[#101010] border-[#E5E5E5] hover:bg-[#F5F5F5]'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>
        )}

        <p className="text-[11px] text-[#737373]">
          Last updated: {formatDateTime(task.updated_at)}
        </p>
      </div>
    </Modal>
  );
}
