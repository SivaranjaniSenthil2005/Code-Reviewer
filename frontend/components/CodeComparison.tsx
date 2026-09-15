"use client";

import React, { useRef, useState } from "react";

interface CodeComparisonProps {
  originalCode: string;
  refactoredCode: string;
  refactoringNotes?: string | null;
  isValidated: boolean;
  language?: string;
}

export const CodeComparison: React.FC<CodeComparisonProps> = ({
  originalCode,
  refactoredCode,
  refactoringNotes,
  isValidated,
  language = "python",
}) => {
  const [activeView, setActiveView] = useState<"side-by-side" | "refactored">("side-by-side");
  const leftPaneRef = useRef<HTMLDivElement>(null);
  const rightPaneRef = useRef<HTMLDivElement>(null);
  const isSyncingRef = useRef(false);

  // Synchronized scrolling
  const handleScroll = (source: "left" | "right") => {
    if (isSyncingRef.current) return;
    isSyncingRef.current = true;

    if (source === "left" && leftPaneRef.current && rightPaneRef.current) {
      rightPaneRef.current.scrollTop = leftPaneRef.current.scrollTop;
      rightPaneRef.current.scrollLeft = leftPaneRef.current.scrollLeft;
    } else if (source === "right" && leftPaneRef.current && rightPaneRef.current) {
      leftPaneRef.current.scrollTop = rightPaneRef.current.scrollTop;
      leftPaneRef.current.scrollLeft = rightPaneRef.current.scrollLeft;
    }

    setTimeout(() => {
      isSyncingRef.current = false;
    }, 50);
  };

  const origLines = originalCode.split("\n");
  const refactLines = (isValidated ? refactoredCode : originalCode).split("\n");

  return (
    <div className="space-y-4">
      {/* Header & Toggle Controls */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">⚡</span>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Refactoring & Code Comparison
          </h3>
        </div>

        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 p-1 rounded-lg text-xs">
          <button
            type="button"
            onClick={() => setActiveView("side-by-side")}
            className={`px-3 py-1 rounded-md font-medium transition-all ${
              activeView === "side-by-side"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Side-by-Side Diff
          </button>
          <button
            type="button"
            onClick={() => setActiveView("refactored")}
            className={`px-3 py-1 rounded-md font-medium transition-all ${
              activeView === "refactored"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Refactored Only
          </button>
        </div>
      </div>

      {/* Fallback Warning if Refactoring wasn't confidently validated */}
      {!isValidated && (
        <div className="p-3.5 rounded-xl border border-amber-500/40 bg-amber-950/30 text-amber-200 text-xs flex items-center gap-2.5">
          <span>⚠️</span>
          <span>
            <strong>Safety Fallback:</strong> Automated refactoring did not pass syntax/intent checks. Original code is preserved to prevent defects.
          </span>
        </div>
      )}

      {/* Refactoring Notes */}
      {refactoringNotes && isValidated && (
        <div className="p-3.5 rounded-xl border border-indigo-500/30 bg-indigo-950/20 text-indigo-200 text-xs font-mono">
          <span className="text-indigo-400 font-bold">Modifications: </span>
          {refactoringNotes}
        </div>
      )}

      {/* Side-by-Side Panes */}
      {activeView === "side-by-side" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Left: Original Code */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/90 overflow-hidden shadow-xl flex flex-col">
            <div className="px-4 py-2 bg-slate-900/80 border-b border-slate-800 text-xs font-mono text-slate-400 flex items-center justify-between">
              <span className="text-rose-400 font-semibold">Original Code</span>
              <span>{origLines.length} lines</span>
            </div>
            <div
              ref={leftPaneRef}
              onScroll={() => handleScroll("left")}
              className="p-3 h-96 overflow-auto font-mono text-xs text-slate-300 leading-6 whitespace-pre"
            >
              {origLines.map((line, idx) => {
                const isDiff = refactLines[idx] !== line;
                return (
                  <div
                    key={idx}
                    className={`flex items-start ${
                      isDiff && isValidated ? "bg-rose-950/30 text-rose-200 -mx-3 px-3" : ""
                    }`}
                  >
                    <span className="select-none text-slate-600 text-right pr-4 w-8 inline-block">
                      {idx + 1}
                    </span>
                    <span className="flex-1">{line || " "}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right: Refactored Code */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/90 overflow-hidden shadow-xl flex flex-col">
            <div className="px-4 py-2 bg-slate-900/80 border-b border-slate-800 text-xs font-mono text-slate-400 flex items-center justify-between">
              <span className="text-emerald-400 font-semibold">
                {isValidated ? "Refactored Code (Validated)" : "Original (Safety Preserved)"}
              </span>
              <span>{refactLines.length} lines</span>
            </div>
            <div
              ref={rightPaneRef}
              onScroll={() => handleScroll("right")}
              className="p-3 h-96 overflow-auto font-mono text-xs text-slate-200 leading-6 whitespace-pre"
            >
              {refactLines.map((line, idx) => {
                const isDiff = origLines[idx] !== line;
                return (
                  <div
                    key={idx}
                    className={`flex items-start ${
                      isDiff && isValidated ? "bg-emerald-950/40 text-emerald-200 -mx-3 px-3" : ""
                    }`}
                  >
                    <span className="select-none text-slate-600 text-right pr-4 w-8 inline-block">
                      {idx + 1}
                    </span>
                    <span className="flex-1">{line || " "}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ) : (
        /* Single Pane View */
        <div className="rounded-xl border border-slate-800 bg-slate-950/90 overflow-hidden shadow-xl">
          <div className="px-4 py-2 bg-slate-900/80 border-b border-slate-800 text-xs font-mono text-emerald-400 font-semibold flex items-center justify-between">
            <span>Refactored Clean Code</span>
            <span className="text-slate-400">{refactLines.length} lines</span>
          </div>
          <div className="p-4 h-96 overflow-auto font-mono text-xs text-slate-200 leading-6 whitespace-pre">
            {refactLines.map((line, idx) => (
              <div key={idx} className="flex items-start">
                <span className="select-none text-slate-600 text-right pr-4 w-8 inline-block">
                  {idx + 1}
                </span>
                <span className="flex-1">{line || " "}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
