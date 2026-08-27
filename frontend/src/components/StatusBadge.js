import { statusColor } from "../lib/format";

export function StatusBadge({ status, testid }) {
  return (
    <span
      data-testid={testid || "status-badge"}
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusColor(status)}`}
    >
      {status}
    </span>
  );
}
