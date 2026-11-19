const dateTime = new Intl.DateTimeFormat("en-GB", {
  timeZone: "UTC",
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

const dateOnly = new Intl.DateTimeFormat("en-GB", { timeZone: "UTC", day: "2-digit", month: "short", year: "numeric" });

/** "21 Oct 2026, 09:15 UTC" */
export function formatDateTime(iso: string): string {
  return `${dateTime.format(new Date(iso))} UTC`;
}

/** "20 Oct 2026" for a calendar date such as completedAt. */
export function formatDate(isoDate: string): string {
  return dateOnly.format(new Date(`${isoDate.slice(0, 10)}T00:00:00Z`));
}

/** Middle-truncates a hash or token: 0x0b9e242b…9ce3 (DESIGN.md, Mono-for-Machines Rule). */
export function middle(value: string, head = 10, tail = 4): string {
  return value.length <= head + tail + 1 ? value : `${value.slice(0, head)}…${value.slice(-tail)}`;
}
