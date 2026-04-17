"use client";

type Status = "MEETS" | "PARTIALLY_MEETS" | "FAILS" | "INSUFFICIENT_DATA" | "FLAG";

interface Props {
  status: Status;
}

const config: Record<Status, { label: string; className: string; dot: string }> = {
  MEETS: {
    label: "Meets",
    className: "bg-emerald-50 text-emerald-700 border-emerald-200",
    dot: "bg-emerald-500",
  },
  PARTIALLY_MEETS: {
    label: "Partial",
    className: "bg-amber-50 text-amber-700 border-amber-200",
    dot: "bg-amber-500",
  },
  FAILS: {
    label: "Fails",
    className: "bg-red-50 text-red-700 border-red-200",
    dot: "bg-red-500",
  },
  FLAG: {
    label: "Flag",
    className: "bg-amber-50 text-amber-700 border-amber-200",
    dot: "bg-amber-400",
  },
  INSUFFICIENT_DATA: {
    label: "Insufficient Data",
    className: "bg-gray-50 text-gray-600 border-gray-200",
    dot: "bg-gray-400",
  },
};

export function ComplianceStatusBadge({ status }: Props) {
  const { label, className, dot } = config[status] ?? config.INSUFFICIENT_DATA;
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium border ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dot}`} />
      {label}
    </span>
  );
}
