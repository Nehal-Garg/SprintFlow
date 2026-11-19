import { AlertTriangle, Inbox } from 'lucide-react';
import { PRIORITY_BADGE_STYLES, STATUS_BADGE_STYLES } from '../../utils/constants';

export function Card({ children, className = '', surface = false }) {
  return (
    <div
      className={`rounded-xl border border-[#E5E5E5] shadow-card ${
        surface ? 'bg-[#F5F5F5]' : 'bg-white'
      } ${className}`}
    >
      {children}
    </div>
  );
}

export function Badge({ children, className = '' }) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${className}`}
    >
      {children}
    </span>
  );
}

export function StatusBadge({ status }) {
  const cls = STATUS_BADGE_STYLES[status] || 'bg-neutral-100 text-[#101010] border-neutral-300';
  return <Badge className={cls}>{status}</Badge>;
}

export function PriorityBadge({ priority }) {
  const cls = PRIORITY_BADGE_STYLES[priority] || 'bg-neutral-100 text-[#101010] border-neutral-300';
  return <Badge className={cls}>{priority}</Badge>;
}

export function ProgressBar({ value = 0, showLabel = true, height = 'h-2' }) {
  const clamped = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <div className="flex items-center gap-2.5 w-full">
      <div className={`flex-1 bg-[#E5E5E5] rounded-full overflow-hidden ${height}`}>
        <div
          className="h-full bg-[#75C900] rounded-full transition-all duration-300"
          style={{ width: `${clamped}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-xs font-semibold text-[#101010] tabular-nums w-11 text-right">
          {clamped.toFixed(0)}%
        </span>
      )}
    </div>
  );
}

export function LoadingSpinner({ label = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-[#737373]">
      <div className="w-8 h-8 border-2 border-[#E5E5E5] border-t-[#75C900] rounded-full animate-spin mb-3" />
      <p className="text-sm font-medium">{label}</p>
    </div>
  );
}

export function EmptyState({ icon: Icon = Inbox, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-12 px-6 border border-dashed border-[#E5E5E5] rounded-xl bg-[#F5F5F5]/60">
      <div className="w-11 h-11 rounded-full bg-white border border-[#E5E5E5] flex items-center justify-center mb-3">
        <Icon className="w-5 h-5 text-[#737373]" />
      </div>
      <h3 className="text-sm font-semibold text-[#101010]">{title}</h3>
      {description && (
        <p className="text-xs text-[#737373] mt-1 max-w-md">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function ErrorBanner({ message, onRetry }) {
  if (!message) return null;
  return (
    <div className="flex items-center justify-between gap-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-[#DC2626]">
      <div className="flex items-center gap-2.5">
        <AlertTriangle className="w-4 h-4 shrink-0" />
        <span>{message}</span>
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="text-xs font-semibold underline hover:no-underline shrink-0"
        >
          Retry
        </button>
      )}
    </div>
  );
}

export function InputField({ label, error, className = '', ...props }) {
  return (
    <div className={className}>
      {label && (
        <label className="block text-xs font-semibold text-[#101010] mb-1.5">
          {label}
          {props.required && <span className="text-[#DC2626] ml-0.5">*</span>}
        </label>
      )}
      <input
        className={`w-full rounded-lg border bg-white px-3 py-2 text-sm text-[#101010] placeholder:text-[#737373] focus:outline-none focus:ring-2 focus:ring-[#75C900] focus:border-[#101010] disabled:bg-[#F5F5F5] ${
          error ? 'border-[#DC2626]' : 'border-[#E5E5E5]'
        }`}
        {...props}
      />
      {error && <p className="text-xs text-[#DC2626] mt-1">{error}</p>}
    </div>
  );
}

export function SelectField({ label, error, children, className = '', ...props }) {
  return (
    <div className={className}>
      {label && (
        <label className="block text-xs font-semibold text-[#101010] mb-1.5">
          {label}
          {props.required && <span className="text-[#DC2626] ml-0.5">*</span>}
        </label>
      )}
      <select
        className={`w-full rounded-lg border bg-white px-3 py-2 text-sm text-[#101010] focus:outline-none focus:ring-2 focus:ring-[#75C900] focus:border-[#101010] disabled:bg-[#F5F5F5] ${
          error ? 'border-[#DC2626]' : 'border-[#E5E5E5]'
        }`}
        {...props}
      >
        {children}
      </select>
      {error && <p className="text-xs text-[#DC2626] mt-1">{error}</p>}
    </div>
  );
}

export function TextareaField({ label, error, className = '', rows = 3, ...props }) {
  return (
    <div className={className}>
      {label && (
        <label className="block text-xs font-semibold text-[#101010] mb-1.5">
          {label}
          {props.required && <span className="text-[#DC2626] ml-0.5">*</span>}
        </label>
      )}
      <textarea
        rows={rows}
        className={`w-full rounded-lg border bg-white px-3 py-2 text-sm text-[#101010] placeholder:text-[#737373] focus:outline-none focus:ring-2 focus:ring-[#75C900] focus:border-[#101010] disabled:bg-[#F5F5F5] ${
          error ? 'border-[#DC2626]' : 'border-[#E5E5E5]'
        }`}
        {...props}
      />
      {error && <p className="text-xs text-[#DC2626] mt-1">{error}</p>}
    </div>
  );
}
