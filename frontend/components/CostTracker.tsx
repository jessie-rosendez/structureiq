"use client";

interface Props {
  callCost: number;
  sessionTotal: number;
  inputTokens: number;
  outputTokens: number;
}

export function CostTracker({ callCost, sessionTotal, inputTokens, outputTokens }: Props) {
  return (
    <div className="rounded-lg border border-border bg-surface-secondary p-3 space-y-2">
      <p className="text-xs font-semibold text-ink-secondary uppercase tracking-wider">
        Usage
      </p>
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs">
          <span className="text-ink-muted">This call</span>
          <span className="font-medium text-ink">${callCost.toFixed(6)}</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-ink-muted">Session total</span>
          <span className="font-medium text-ink">${sessionTotal.toFixed(4)}</span>
        </div>
        <div className="border-t border-border pt-1.5 flex justify-between text-xs">
          <span className="text-ink-subtle">Tokens in / out</span>
          <span className="text-ink-muted font-mono">
            {inputTokens.toLocaleString()} / {outputTokens.toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
}
