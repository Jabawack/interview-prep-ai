"use client";

import type { UsageData } from "@/types";

function formatTokens(n: number): string {
  return n.toLocaleString();
}

function formatCost(usd: number): string {
  if (usd === 0) return "$0.00";
  if (usd < 0.0001) return `<$0.0001`;
  return `$${usd.toFixed(4)}`;
}

export function UsageReport({ usage }: { usage: UsageData }) {
  return (
    <div className="mt-1.5 flex items-center gap-1.5 text-xs text-zinc-400 dark:text-zinc-500">
      <span className="font-medium">{usage.model}</span>
      <span>&middot;</span>
      <span className="font-mono">{formatTokens(usage.total_tokens)} tokens</span>
      <span>&middot;</span>
      <span className="font-mono">
        {usage.llm_calls} {usage.llm_calls === 1 ? "call" : "calls"}
      </span>
      <span>&middot;</span>
      <span className="font-mono">{formatCost(usage.cost_usd)}</span>
    </div>
  );
}
