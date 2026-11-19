export const PROJECT_STATUSES = ['Planning', 'Active', 'On Hold', 'Completed'];
export const STORY_STATUSES = ['Backlog', 'To Do', 'In Progress', 'Done'];
export const TASK_STATUSES = ['To Do', 'In Progress', 'In Review', 'Done'];
export const PRIORITIES = ['Low', 'Medium', 'High', 'Critical'];

export const STATUS_BADGE_STYLES = {
  Planning: 'bg-neutral-100 text-[#101010] border-neutral-300',
  Active: 'bg-[#75C900]/15 text-[#101010] border-[#75C900]',
  'On Hold': 'bg-amber-50 text-amber-800 border-amber-300',
  Completed: 'bg-green-50 text-[#16A34A] border-green-300',
  Backlog: 'bg-neutral-100 text-[#737373] border-neutral-300',
  'To Do': 'bg-neutral-100 text-[#101010] border-neutral-300',
  'In Progress': 'bg-[#75C900]/20 text-[#101010] border-[#75C900]',
  'In Review': 'bg-amber-50 text-amber-800 border-amber-300',
  Done: 'bg-green-50 text-[#16A34A] border-green-300',
};

export const PRIORITY_BADGE_STYLES = {
  Low: 'bg-neutral-100 text-[#737373] border-neutral-200',
  Medium: 'bg-neutral-100 text-[#101010] border-neutral-300',
  High: 'bg-amber-50 text-amber-800 border-amber-300',
  Critical: 'bg-red-50 text-[#DC2626] border-red-300',
};

export const NOTIFICATION_TYPE_META = {
  upcoming_deadline: {
    label: 'Upcoming Deadline',
    badgeClass: 'bg-amber-50 text-amber-800 border-amber-300',
  },
  overdue_task: {
    label: 'Overdue Task',
    badgeClass: 'bg-red-50 text-[#DC2626] border-red-300',
  },
  task_assignment: {
    label: 'Task Assignment',
    badgeClass: 'bg-[#75C900]/15 text-[#101010] border-[#75C900]',
  },
};

export const ACTIVITY_ACTION_LABELS = {
  project_created: 'Project Created',
  project_updated: 'Project Updated',
  project_deleted: 'Project Deleted',
  story_created: 'Story Created',
  story_updated: 'Story Updated',
  story_deleted: 'Story Deleted',
  task_created: 'Task Created',
  task_updated: 'Task Updated',
  task_assigned: 'Task Assigned',
  task_status_changed: 'Status Changed',
  task_completed: 'Task Completed',
  task_deleted: 'Task Deleted',
};
