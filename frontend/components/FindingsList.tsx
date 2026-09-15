"use client";

import React, { useMemo } from "react";

export interface IssueFinding {
  line?: number | null;
  category: "bug" | "vulnerability" | "style" | "performance" | string;
  severity: "low" | "medium" | "high" | "critical" | string;
  description: string;
  suggestion?: string | null;
}

interface FindingsListProps {
  issues: IssueFinding[];
}

const SEVERITY_STYLES: Record<string, { badge: string; bg: string; border: string }> = {
  critical: {
    badge: "bg-rose-500/20 text-rose-300 border-rose-500/40",
    bg: "bg-rose-950/20",
    border: "border-rose-900/40",
  },
  high: {
    badge: "bg-amber-500/20 text-amber-300 border-amber-500/40",
    bg: "bg-amber-950/20",
    border: "border-amber-900/40",
  },
  medium: {
    badge: "bg-yellow-500/20 text-yellow-300 border-yellow-500/40",
    bg: "bg-yellow-950/20",
    border: "border-yellow-900/40",
  },
  low: {
    badge: "bg-blue-500/20 text-blue-300 border-blue-500/40",
    bg: "bg-blue-950/20",
    border: "border-blue-900/40",
  },
};

const SEVERITY_WEIGHT: Record<string, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
};

export const FindingsList: React.FC<FindingsListProps> = ({ issues }) => {
  const sortedIssues = useMemo(() => {
    return [...issues].sort((a, b) => {
      const wA = SEVERITY_WEIGHT[a.severity.toLowerCase()] || 0;
      const wB = SEVERITY_WEIGHT[b.severity.toLowerCase()] || 0;
      if (wB !== wA) return wB - wA;
      return (a.line || 0) - (b.line || 0);
    });
  }, [issues]);

  if (!issues || issues.length === 0) {
    return (
      <div className="p-6 rounded-xl border border-emerald-800/40 bg-emerald-950/20 text-emerald-300 text-sm flex items-center gap-3">
        <span className="text-xl">✨</span>
        <div>
          <div className="font-semibold">Clean Code!</div>
          <div className="text-xs text-emerald-400/80">No bugs or security vulnerabilities were identified.</div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-xs text-slate-400 pb-1">
        <span>Identified Findings ({issues.length})</span>
        <span>Sorted by Severity</span>
      </div>

      <div className="space-y-2.5">
        {sortedIssues.map((issue, idx) => {
          const sevKey = issue.severity.toLowerCase();
          const style = SEVERITY_STYLES[sevKey] || SEVERITY_STYLES.medium;

          return (
            <div
              key={idx}
              className={`p-4 rounded-xl border ${style.border} ${style.bg} backdrop-blur-sm transition-all hover:translate-x-0.5`}
            >
              <div className="flex items-center gap-2 mb-2 flex-wrap">
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border ${style.badge}`}
                >
                  {issue.severity}
                </span>

                <span className="px-2 py-0.5 rounded text-[10px] uppercase font-mono tracking-wide bg-slate-800/80 text-slate-300 border border-slate-700/60">
                  {issue.category}
                </span>

                {issue.line && (
                  <span className="text-xs font-mono text-slate-400 bg-slate-900/60 px-2 py-0.5 rounded border border-slate-800">
                    Line {issue.line}
                  </span>
                )}
              </div>

              <p className="text-sm text-slate-200 leading-relaxed">{issue.description}</p>

              {issue.suggestion && (
                <div className="mt-2.5 p-2.5 rounded-lg bg-slate-900/80 border border-slate-800/80 text-xs text-indigo-300 flex items-start gap-2 font-mono">
                  <span className="text-indigo-400">💡 Fix:</span>
                  <span className="text-slate-300">{issue.suggestion}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
