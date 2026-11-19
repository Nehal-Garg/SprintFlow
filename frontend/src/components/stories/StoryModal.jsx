import { useEffect, useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { InputField, SelectField, TextareaField } from '../common/UI';
import { PRIORITIES, STORY_STATUSES } from '../../utils/constants';
import { extractErrorMessage } from '../../utils/formatters';

const INITIAL_FORM = {
  title: '',
  description: '',
  acceptance_criteria: '',
  priority: 'Medium',
  status: 'Backlog',
  story_points: '',
  assigned_to: '',
  due_date: '',
};

export function StoryModal({ open, onClose, initialData = null, members = [], onSubmit }) {
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
          acceptance_criteria: initialData.acceptance_criteria || '',
          priority: initialData.priority || 'Medium',
          status: initialData.status || 'Backlog',
          story_points:
            initialData.story_points !== null && initialData.story_points !== undefined
              ? String(initialData.story_points)
              : '',
          assigned_to: initialData.assigned_to ? String(initialData.assigned_to) : '',
          due_date: initialData.due_date || '',
        });
      } else {
        setForm(INITIAL_FORM);
      }
    }
  }, [open, initialData]);

  const validate = () => {
    const next = {};
    if (!form.title.trim() || form.title.trim().length < 2) {
      next.title = 'Story title must be at least 2 characters.';
    }
    if (form.story_points !== '' && (Number(form.story_points) < 0 || Number.isNaN(Number(form.story_points)))) {
      next.story_points = 'Story points must be 0 or greater.';
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
        acceptance_criteria: form.acceptance_criteria.trim() || null,
        priority: form.priority,
        status: form.status,
        story_points: form.story_points === '' ? null : Number(form.story_points),
        assigned_to: form.assigned_to ? Number(form.assigned_to) : null,
        due_date: form.due_date || null,
      };
      await onSubmit(payload);
      onClose();
    } catch (err) {
      setApiError(extractErrorMessage(err, 'Failed to save user story.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={isEdit ? 'Edit User Story' : 'Create User Story'}
      subtitle="Define user-facing value and acceptance criteria inside this project."
      maxWidth="max-w-xl"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {apiError && (
          <div className="rounded-lg bg-red-50 border border-red-200 px-3.5 py-2.5 text-xs text-[#DC2626]">
            {apiError}
          </div>
        )}

        <InputField
          label="Story Title"
          required
          placeholder="e.g., User Authentication"
          value={form.title}
          onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
          error={errors.title}
        />

        <TextareaField
          label="Description"
          placeholder="As a user, I want to..."
          value={form.description}
          onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
          rows={2}
        />

        <TextareaField
          label="Acceptance Criteria"
          placeholder="Given / When / Then criteria for marking this story Done..."
          value={form.acceptance_criteria}
          onChange={(e) => setForm((f) => ({ ...f, acceptance_criteria: e.target.value }))}
          rows={3}
        />

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
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
            {STORY_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </SelectField>

          <InputField
            label="Story Points"
            type="number"
            min="0"
            max="100"
            placeholder="e.g., 5"
            value={form.story_points}
            onChange={(e) => setForm((f) => ({ ...f, story_points: e.target.value }))}
            error={errors.story_points}
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <SelectField
            label="Assigned User"
            value={form.assigned_to}
            onChange={(e) => setForm((f) => ({ ...f, assigned_to: e.target.value }))}
          >
            <option value="">Unassigned</option>
            {members.map((m) => (
              <option key={m.user_id} value={m.user_id}>
                {m.full_name} ({m.role})
              </option>
            ))}
          </SelectField>

          <InputField
            label="Due Date"
            type="date"
            value={form.due_date}
            onChange={(e) => setForm((f) => ({ ...f, due_date: e.target.value }))}
          />
        </div>

        <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-[#E5E5E5]">
          <Button variant="secondary" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button type="submit" loading={submitting}>
            {isEdit ? 'Save Story' : 'Create Story'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
