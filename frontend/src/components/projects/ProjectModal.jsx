import { useEffect, useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { InputField, SelectField, TextareaField } from '../common/UI';
import { PROJECT_STATUSES } from '../../utils/constants';
import { extractErrorMessage } from '../../utils/formatters';

const INITIAL_FORM = {
  name: '',
  description: '',
  start_date: '',
  end_date: '',
  status: 'Planning',
};

export function ProjectModal({ open, onClose, initialData = null, onSubmit }) {
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
          name: initialData.name || '',
          description: initialData.description || '',
          start_date: initialData.start_date || '',
          end_date: initialData.end_date || '',
          status: initialData.status || 'Planning',
        });
      } else {
        setForm(INITIAL_FORM);
      }
    }
  }, [open, initialData]);

  const validate = () => {
    const next = {};
    if (!form.name.trim() || form.name.trim().length < 2) {
      next.name = 'Project name must be at least 2 characters.';
    }
    if (form.start_date && form.end_date && form.end_date < form.start_date) {
      next.end_date = 'Deadline cannot be earlier than start date.';
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
        name: form.name.trim(),
        description: form.description.trim() || null,
        start_date: form.start_date || null,
        end_date: form.end_date || null,
        status: form.status,
      };
      await onSubmit(payload);
      onClose();
    } catch (err) {
      setApiError(extractErrorMessage(err, 'Failed to save project.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={isEdit ? 'Edit Project' : 'Create New Project'}
      subtitle={
        isEdit
          ? 'Update project scope, status, or schedule.'
          : 'Organize user stories and tasks under a new team project.'
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {apiError && (
          <div className="rounded-lg bg-red-50 border border-red-200 px-3.5 py-2.5 text-xs text-[#DC2626]">
            {apiError}
          </div>
        )}

        <InputField
          label="Project Name"
          required
          placeholder="e.g., E-Commerce Platform"
          value={form.name}
          onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          error={errors.name}
        />

        <TextareaField
          label="Description"
          placeholder="Brief overview of goals and deliverables..."
          value={form.description}
          onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
          rows={3}
        />

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <InputField
            label="Start Date"
            type="date"
            value={form.start_date}
            onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))}
          />
          <InputField
            label="Deadline (End Date)"
            type="date"
            value={form.end_date}
            onChange={(e) => setForm((f) => ({ ...f, end_date: e.target.value }))}
            error={errors.end_date}
          />
        </div>

        <SelectField
          label="Status"
          value={form.status}
          onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
        >
          {PROJECT_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </SelectField>

        <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-[#E5E5E5]">
          <Button variant="secondary" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button type="submit" loading={submitting}>
            {isEdit ? 'Save Changes' : 'Create Project'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
