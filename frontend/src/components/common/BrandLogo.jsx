export function BrandLogo({ dark = true, size = 'md' }) {
  const textSize = size === 'lg' ? 'text-2xl' : 'text-lg';
  const boxSize = size === 'lg' ? 'w-9 h-9' : 'w-8 h-8';

  return (
    <div className="inline-flex items-center gap-2.5 select-none">
      <div
        className={`${boxSize} rounded-lg flex items-center justify-center shrink-0 ${
          dark ? 'bg-[#75C900]' : 'bg-[#101010]'
        }`}
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          className="w-5 h-5"
          aria-hidden="true"
        >
          <path
            d="M4 7.5H14.5L11.5 4.5M20 16.5H9.5L12.5 19.5M4 12H18"
            stroke={dark ? '#101010' : '#75C900'}
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
      <div className="leading-none">
        <span
          className={`${textSize} font-bold tracking-tight ${
            dark ? 'text-white' : 'text-[#101010]'
          }`}
        >
          Sprint<span className="text-[#75C900]">Flow</span>
        </span>
      </div>
    </div>
  );
}
