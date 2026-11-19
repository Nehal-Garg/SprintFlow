export function Button({
  children,
  variant = 'primary',
  size = 'md',
  type = 'button',
  disabled = false,
  loading = false,
  className = '',
  ...props
}) {
  const base =
    'inline-flex items-center justify-center gap-2 font-semibold rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-[#75C900] disabled:cursor-not-allowed';

  const sizes = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-5 py-2.5 text-sm',
  };

  const variants = {
    primary:
      'bg-[#75C900] text-[#101010] hover:bg-[#66B000] disabled:bg-neutral-200 disabled:text-neutral-500',
    secondary:
      'bg-white text-[#101010] border border-[#101010] hover:bg-[#F5F5F5] disabled:bg-neutral-100 disabled:text-neutral-400 disabled:border-neutral-300',
    subtle:
      'bg-[#F5F5F5] text-[#101010] border border-[#E5E5E5] hover:bg-neutral-200 disabled:opacity-50',
    destructive:
      'bg-[#DC2626] text-white hover:bg-red-700 disabled:bg-neutral-200 disabled:text-neutral-500',
    ghost:
      'bg-transparent text-[#101010] hover:bg-[#F5F5F5] disabled:text-neutral-400',
  };

  return (
    <button
      type={type}
      disabled={disabled || loading}
      className={`${base} ${sizes[size]} ${variants[variant]} ${className}`}
      {...props}
    >
      {loading && (
        <span className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
      )}
      {children}
    </button>
  );
}
