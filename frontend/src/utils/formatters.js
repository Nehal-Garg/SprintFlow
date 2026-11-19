export function formatDate(dateStr) {
  if (!dateStr) return '—';
  const parsed = new Date(dateStr.includes('T') ? dateStr : `${dateStr}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return dateStr;
  return parsed.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function parseUtcTimestamp(dateStr) {
  if (!dateStr) return null;
  const hasTz = /(?:Z|[+-]\d{2}:\d{2})$/i.test(dateStr);
  const normalized = dateStr.includes('T') && !hasTz ? `${dateStr}Z` : dateStr;
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export function formatDateTime(dateStr) {
  if (!dateStr) return '—';
  const parsed = parseUtcTimestamp(dateStr);
  if (!parsed) return dateStr;
  return parsed.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatRelativeTime(dateStr) {
  if (!dateStr) return '';
  const parsed = parseUtcTimestamp(dateStr);
  if (!parsed) return '';
  const diffSec = Math.max(0, Math.floor((Date.now() - parsed.getTime()) / 1000));
  if (diffSec < 60) return 'Just now';
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 7) return `${diffDay}d ago`;
  return formatDate(dateStr);
}

export function isDueSoon(dateStr, status) {
  if (!dateStr || status === 'Done') return false;
  const due = new Date(`${dateStr}T00:00:00`);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diffDays = Math.ceil((due - today) / (1000 * 60 * 60 * 24));
  return diffDays >= 0 && diffDays <= 3;
}

export function extractErrorMessage(error, fallback = 'An unexpected error occurred.') {
  const data = error?.response?.data;
  if (!data) {
    if (error?.message === 'Network Error') {
      return 'Unable to reach SprintFlow API. Make sure the backend server is running.';
    }
    return error?.message || fallback;
  }
  if (Array.isArray(data.errors) && data.errors.length > 0) {
    return data.errors.map((e) => e.message).join(' ');
  }
  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.detail) && data.detail.length > 0) {
    return data.detail.map((d) => d.msg || String(d)).join(' ');
  }
  return fallback;
}

export function getInitials(name) {
  if (!name) return 'SF';
  const parts = name.trim().split(/\s+/);
  return parts
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() || '')
    .join('');
}
