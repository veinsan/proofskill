// One authored icon set: 16px grid, 1.5px stroke, round joins. Colors follow currentColor.

interface IconProps {
  size?: number;
  label?: string;
}

function a11y(label?: string) {
  return label ? { role: "img", "aria-label": label } : { "aria-hidden": true as const };
}

/** A passed check: a filled dot. */
export function DotIcon({ size = 14, label }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 14 14" {...a11y(label)}>
      <circle cx="7" cy="7" r="7" fill="currentColor" />
    </svg>
  );
}

/** A failed check or an error: a hollow ring. */
export function RingIcon({ size = 14, label }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 14 14" {...a11y(label)}>
      <circle cx="7" cy="7" r="6" fill="none" stroke="currentColor" strokeWidth="2" />
    </svg>
  );
}

export function ArrowRightIcon({ size = 22, label }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 22 22" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...a11y(label)}>
      <path d="M3 11h16M13 5l6 6-6 6" />
    </svg>
  );
}

export function CopyIcon({ size = 16, label }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" {...a11y(label)}>
      <rect x="5.25" y="5.25" width="8" height="8" rx="1.5" />
      <path d="M10.75 5.25V3.5a1.25 1.25 0 0 0-1.25-1.25H3.5A1.25 1.25 0 0 0 2.25 3.5v6a1.25 1.25 0 0 0 1.25 1.25h1.75" />
    </svg>
  );
}

export function DownloadIcon({ size = 16, label }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...a11y(label)}>
      <path d="M8 2.5v8M4.5 7.5 8 11l3.5-3.5M2.5 13.5h11" />
    </svg>
  );
}
