"use client";

import React from "react";

interface ComplexityCardProps {
  complexityAssessment: string;
  readabilityScore: number;
}

export const ComplexityCard: React.FC<ComplexityCardProps> = ({
  complexityAssessment,
  readabilityScore,
}) => {
  const normalizedScore = Math.min(100, Math.max(0, readabilityScore));

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-emerald-400 border-emerald-500/30 bg-emerald-500/10";
    if (score >= 60) return "text-yellow-400 border-yellow-500/30 bg-yellow-500/10";
    return "text-rose-400 border-rose-500/30 bg-rose-500/10";
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Readability Score Metric */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-md flex flex-col justify-between">
        <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
          Readability Score
        </div>
        <div className="my-2 flex items-baseline gap-2">
          <span className="text-4xl font-extrabold tracking-tight text-white">
            {normalizedScore.toFixed(1)}
          </span>
          <span className="text-xs text-slate-500">/ 100</span>
        </div>
        {/* Progress Bar */}
        <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              normalizedScore >= 80
                ? "bg-emerald-500"
                : normalizedScore >= 60
                ? "bg-yellow-500"
                : "bg-rose-500"
            }`}
            style={{ width: `${normalizedScore}%` }}
          />
        </div>
      </div>

      {/* Complexity Assessment */}
      <div className="md:col-span-2 p-4 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-md flex flex-col justify-between">
        <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">
          Complexity & Structural Assessment
        </div>
        <p className="text-sm text-slate-200 leading-relaxed font-mono text-xs">
          {complexityAssessment || "Algorithmic complexity assessment not available."}
        </p>
      </div>
    </div>
  );
};
