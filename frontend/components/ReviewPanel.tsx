"use client";

import React from "react";
import { FindingsList, IssueFinding } from "./FindingsList";
import { ComplexityCard } from "./ComplexityCard";
import { CodeComparison } from "./CodeComparison";
import { ExportButton } from "./ExportButton";

export interface ReviewData {
  review_id?: string | null;
  detected_language: string;
  summary: string;
  explanation: string;
  issues: IssueFinding[];
  refactored_code: string;
  refactoring_notes?: string | null;
  refactoring_validated: boolean;
  complexity_assessment: string;
  readability_score: number;
  review_mode: string;
  processing_time_ms?: number;
}

interface ReviewPanelProps {
  data: ReviewData;
  originalCode: string;
}

export const ReviewPanel: React.FC<ReviewPanelProps> = ({ data, originalCode }) => {
  return (
    <div className="space-y-6">
      {/* Executive Summary Card */}
      <div className="p-5 rounded-2xl border border-indigo-500/30 bg-gradient-to-r from-indigo-950/40 via-purple-950/30 to-slate-950/50 backdrop-blur-md shadow-xl">
        <div className="flex items-center justify-between gap-4 mb-2 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="text-xl">📊</span>
            <h2 className="text-base font-bold text-white tracking-tight">Review Summary</h2>
          </div>
          <div className="flex items-center gap-2">
            <ExportButton data={data} originalCode={originalCode} />
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase tracking-wider">
              {data.review_mode} Mode
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono bg-slate-800 text-slate-300 border border-slate-700">
              {data.detected_language}
            </span>
            {data.processing_time_ms && (
              <span className="text-xs font-mono text-slate-400">
                {data.processing_time_ms.toFixed(0)}ms
              </span>
            )}
          </div>
        </div>
        <p className="text-sm text-slate-200 leading-relaxed">{data.summary}</p>
      </div>

      {/* Code Explanation */}
      <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-md">
        <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2 flex items-center gap-2">
          <span>💡</span> Code Analysis & Architecture
        </div>
        <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
          {data.explanation}
        </p>
      </div>

      {/* Complexity & Readability */}
      <ComplexityCard
        complexityAssessment={data.complexity_assessment}
        readabilityScore={data.readability_score}
      />

      {/* Issues & Findings */}
      <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-md">
        <FindingsList issues={data.issues} />
      </div>

      {/* Side-by-Side Code Comparison & Refactoring */}
      <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-md">
        <CodeComparison
          originalCode={originalCode}
          refactoredCode={data.refactored_code}
          refactoringNotes={data.refactoring_notes}
          isValidated={data.refactoring_validated}
          language={data.detected_language}
        />
      </div>
    </div>
  );
};
