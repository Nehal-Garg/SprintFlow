import { createContext, useCallback, useContext, useState } from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

const ToastContext = createContext(null);

let toastSeq = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const dismiss = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const pushToast = useCallback(
    (message, type = 'success', durationMs = 3600) => {
      const id = ++toastSeq;
      setToasts((prev) => [...prev, { id, message, type }]);
      if (durationMs > 0) {
        setTimeout(() => dismiss(id), durationMs);
      }
      return id;
    },
    [dismiss]
  );

  const toast = {
    success: (msg) => pushToast(msg, 'success'),
    error: (msg) => pushToast(msg, 'error', 5000),
    info: (msg) => pushToast(msg, 'info'),
  };

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none px-4 sm:px-0">
        {toasts.map((t) => {
          const styles =
            t.type === 'error'
              ? 'bg-[#101010] text-white border-l-4 border-[#DC2626]'
              : t.type === 'info'
                ? 'bg-[#101010] text-white border-l-4 border-neutral-400'
                : 'bg-[#101010] text-white border-l-4 border-[#75C900]';
          const Icon =
            t.type === 'error'
              ? AlertCircle
              : t.type === 'info'
                ? Info
                : CheckCircle2;
          const iconColor =
            t.type === 'error'
              ? 'text-[#DC2626]'
              : t.type === 'info'
                ? 'text-neutral-300'
                : 'text-[#75C900]';

          return (
            <div
              key={t.id}
              className={`pointer-events-auto flex items-start gap-3 rounded-lg px-4 py-3 shadow-elevated ${styles}`}
              role="status"
            >
              <Icon className={`w-5 h-5 shrink-0 mt-0.5 ${iconColor}`} />
              <p className="text-sm font-medium leading-snug flex-1">{t.message}</p>
              <button
                type="button"
                onClick={() => dismiss(t.id)}
                className="text-neutral-400 hover:text-white transition-colors"
                aria-label="Dismiss notification"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used inside ToastProvider');
  return ctx;
}
