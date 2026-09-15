"use client";

import React from "react";

export type ReviewDepth = "quick" | "deep";

interface ReviewModeSelectorProps {
  mode: ReviewDepth;
  onChange: (mode: ReviewDepth) => void;
  disabled?: boolean;
}

export const ReviewModeSelector: React.FC<ReviewModeSelectorProps> = ({
  mode,
  onChange,
  disabled = false,
}) => {
  return (
    <div className="flex items-center gap-2 p-1 bg-slate-900/80 border border-slate-800 rounded-xl">
      <button
        type="button"
        id="mode-quick-btn"
        disabled={disabled}
        onClick={() => onChange("quick")}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
          mode === "quick"
            ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/25"
            : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
        }`}
      >
        <span>⚡</span>
        <div className="text-left">
          <div className="font-semibold">Quick Scan</div>
          <div className="text-[10px] opacity-75">Fast syntax & logic check</div>
        </div>
      </button>

      <button
        type="button"
        id="mode-deep-btn"
        disabled={disabled}
        onClick={() => onChange("deep")}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
          mode === "deep"
            ? "bg-purple-600 text-white shadow-lg shadow-purple-500/25"
            : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
        }`}
      >
        <span>🔬</span>
        <div className="text-left">
          <div className="font-semibold">Deep Review</div>
          <div className="text-[10px] opacity-75">Full multi-agent + RAG + refactor</div>
        </div>
      </button>
    </div>
  );
};
