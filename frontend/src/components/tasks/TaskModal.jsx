import { useEffect, useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { InputField, SelectField, TextareaField } from '../common/UI';
import { PRIORITIES, TASK_STATUSES } from '../../utils/constants';
import { extractErrorMessage } from '../../utils/formatters';

const INITIAL_FORM = {
  title: '',
  description: '',
  assignee_id: '',
  priority: 'Medium',
  status: 'To Do',
  start_date: '',
  due_date: '',
  estimated_hours: '',
  actual_hours: '',
};

export function TaskModal({
  open,
  onClose,
  initialData = null,
  storyTitle = '',
  members = [],
  onSubmit,
}) {
  const [form, setForm] = useState(INITIAL_FORM);
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const isEdit = Boolean(initialData);

  useEffect(() => {
    if (open) {
      setErrors({});
      setApiError('');
      if (initialData) {
        setForm({
          title: initialData.title || '',
          description: initialData.description || '',
          assignee_id: initialData.assignee_id ? String(initialData.assignee_id) : '',
          priority: initialData.priority || 'Medium',
          status: initialData.status || 'To Do',
          start_date: initialData.start_date || '',
          due_date: initialData.due_date || '',
          estimated_hours:
            initialData.estimated_hours !== null && initialData.estimated_hours !== undefined
              ? String(initialData.estimated_hours)
              : '',
          actual_hours:
            initialData.actual_hours !== null && initialData.actual_hours !== undefined
              ? String(initialData.actual_hours)
              : '',
        });
      } else {
        setForm(INITIAL_FORM);
      }
    }
  }, [open, initialData]);

  const validate = () => {
    const next = {};
    if (!form.title.trim() || form.title.trim().length < 2) {
      next.title = 'Task title must be at least 2 characters.';
    }
    if (form.start_date && form.due_date && form.due_date < form.start_date) {
      next.due_date = 'Due date cannot be earlier than start date.';
    }
    if (form.estimated_hours !== '' && Number(form.estimated_hours) < 0) {
      next.estimated_hours = 'Estimated hours cannot be negative.';
    }
    if (form.actual_hours !== '' && Number(form.actual_hours) < 0) {
      next.actual_hours = 'Actual hours cannot be negative.';
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    setApiError('');
    try {
      const payload = {
        title: form.title.trim(),
        description: form.description.trim() || null,
        assignee_id: form.assignee_id ? Number(form.assignee_id) : null,
        priority: form.priority,
        status: form.status,
        start_date: form.start_date || null,
        due_date: form.due_date || null,
        estimated_hours:
          form.estimated_hours === '' ? null : Number(form.estimated_hours),
        actual_hours: form.actual_hours === '' ? null : Number(form.actual_hours),
      };
      await onSubmit(payload);
      onClose();
    } catch (err) {
      setApiError(extractErrorMessage(err, 'Failed to save task.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={isEdit ? 'Edit Task' : 'Create Task'}
      subtitle={storyTitle ? `User Story: ${storyTitle}` : 'Manage task details and effort tracking.'}
      maxWidth="max-w-xl"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {apiError && (
          <div className="rounded-lg bg-red-50 border border-red-200 px-3.5 py-2.5 text-xs text-[#DC2626]">
            {apiError}
          </div>
        )}

        <InputField
          label="Task Title"
          required
          placeholder="e.g., Develop registration API"
          value={form.title}
          onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
          error={errors.title}
        />

        <TextareaField
          label="Description"
          placeholder="Implementation notes, edge cases, or links..."
          value={form.description}
          onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
          rows={3}
        />

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <SelectField
            label="Assignee"
            value={form.assignee_id}
            onChange={(e) => setForm((f) => ({ ...f, assignee_id: e.target.value }))}
          >
            <option value="">Unassigned</option>
            {members.map((m) => (
              <option key={m.user_id} value={m.user_id}>
                {m.full_name}
              </option>
            ))}
          </SelectField>

          <SelectField
            label="Priority"
            value={form.priority}
            onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </SelectField>

          <SelectField
            label="Status"
            value={form.status}
            onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
          >
            {TASK_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </SelectField>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <InputField
            label="Start Date"
            type="date"
            value={form.start_date}
            onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))}
          />
          <InputField
            label="Due Date"
            type="date"
            value={form.due_date}
            onChange={(e) => setForm((f) => ({ ...f, due_date: e.target.value }))}
            error={errors.due_date}
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <InputField
            label="Estimated Hours"
            type="number"
            step="0.5"
            min="0"
            placeholder="e.g., 4.0"
            value={form.estimated_hours}
            onChange={(e) => setForm((f) => ({ ...f, estimated_hours: e.target.value }))}
            error={errors.estimated_hours}
          />
          <InputField
            label="Actual Hours"
            type="number"
            step="0.5"
            min="0"
            placeholder="e.g., 2.5"
            value={form.actual_hours}
            onChange={(e) => setForm((f) => ({ ...f, actual_hours: e.target.value }))}
            error={errors.actual_hours}
          />
        </div>

        <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-[#E5E5E5]">
          <Button variant="secondary" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button type="submit" loading={submitting}>
            {isEdit ? 'Save Task' : 'Create Task'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
