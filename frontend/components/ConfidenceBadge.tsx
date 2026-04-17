"use client";

interface Props {
  confidence: "HIGH" | "MEDIUM" | "LOW";
}

const styles: Record<string, string> = {
  HIGH: "bg-emerald-50 text-emerald-700 border-emerald-200 ring-emerald-100",
  MEDIUM: "bg-amber-50 text-amber-700 border-amber-200 ring-amber-100",
  LOW: "bg-red-50 text-red-700 border-red-200 ring-red-100",
};

const dots: Record<string, string> = {
  HIGH: "bg-emerald-500",
  MEDIUM: "bg-amber-500",
  LOW: "bg-red-500",
};

export function ConfidenceBadge({ confidence }: Props) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium border ${styles[confidence]}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dots[confidence]}`} />
      {confidence}
    </span>
  );
}
