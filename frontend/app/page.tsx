"use client";

import React, { useState } from "react";
import { CodeEditor } from "@/components/CodeEditor";
import { ReviewModeSelector, ReviewDepth } from "@/components/ReviewModeSelector";
import { ReviewPanel, ReviewData } from "@/components/ReviewPanel";

const DEFAULT_SAMPLE_CODE = `def process_user_query(db_conn, username):
    # Retrieve user profile and calculate discounted score
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor = db_conn.cursor()
    cursor.execute(query)
    user = cursor.fetchone()
    
    score = user['raw_score'] / user['total_attempts']
    return score
`;

export default function Home() {
  const [code, setCode] = useState(DEFAULT_SAMPLE_CODE);
  const [mode, setMode] = useState<ReviewDepth>("quick");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reviewResult, setReviewResult] = useState<ReviewData | null>(null);

  const handleRunReview = async () => {
    if (!code.trim()) {
      setError("Please paste or type code before running the review.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiBase}/api/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: code,
          depth: mode,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        const errorMsg =
          data.detail || data.message || "Failed to complete code review. Please try again.";
        setError(errorMsg);
        return;
      }

      setReviewResult(data);
    } catch (err: any) {
      setError(
        "Could not connect to the backend review service. Please verify the FastAPI server is running."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 selection:bg-indigo-500/30">
      {/* Background Subtle Gradient Glow */}
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.15),rgba(255,255,255,0))] pointer-events-none" />

      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-30 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-indigo-500/30">
            ⚡
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-2">
              AI Code Reviewer & Refactor Platform
            </h1>
            <p className="text-xs text-slate-400">
              Multi-Agent Orchestrated Static Code Analysis
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <ReviewModeSelector mode={mode} onChange={setMode} disabled={loading} />
        </div>
      </header>

      {/* Main Workspace */}
      <div className="max-w-7xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Code Input & Action Controls */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-semibold uppercase tracking-wider">Source Code Input</span>
            <button
              type="button"
              onClick={() => setCode("")}
              disabled={loading}
              className="hover:text-slate-200 transition-colors text-[11px]"
            >
              Clear
            </button>
          </div>

          <CodeEditor
            value={code}
            onChange={setCode}
            disabled={loading}
            language="auto-detect"
          />

          {/* Error Banner */}
          {error && (
            <div className="p-4 rounded-xl border border-rose-500/40 bg-rose-950/30 text-rose-200 text-xs flex items-start gap-3 backdrop-blur-sm animate-fadeIn">
              <span className="text-base text-rose-400">⚠️</span>
              <div className="flex-1">
                <div className="font-semibold">Review Error</div>
                <div className="mt-0.5 text-rose-300/80 leading-relaxed">{error}</div>
              </div>
            </div>
          )}

          {/* Submit Button */}
          <button
            id="run-review-btn"
            type="button"
            onClick={handleRunReview}
            disabled={loading}
            className={`w-full py-3.5 px-6 rounded-xl font-semibold text-sm transition-all flex items-center justify-center gap-2 shadow-xl ${
              loading
                ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700"
                : mode === "quick"
                ? "bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white shadow-indigo-500/25 active:scale-[0.99]"
                : "bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-purple-500/25 active:scale-[0.99]"
            }`}
          >
            {loading ? (
              <>
                <svg
                  className="animate-spin h-4 w-4 text-slate-400"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8v8H4z"
                  />
                </svg>
                <span>Analyzing with {mode === "deep" ? "8 Agents..." : "Fast Agents..."}</span>
              </>
            ) : (
              <>
                <span>🚀</span>
                <span>Run {mode === "quick" ? "Quick Scan" : "Deep Review"}</span>
              </>
            )}
          </button>
        </div>

        {/* Right Column: Review Results Panel */}
        <div className="lg:col-span-7">
          {reviewResult ? (
            <ReviewPanel data={reviewResult} originalCode={code} />
          ) : (
            <div className="h-full min-h-[400px] rounded-2xl border border-dashed border-slate-800/80 bg-slate-900/20 backdrop-blur-sm flex flex-col items-center justify-center p-8 text-center">
              <div className="h-16 w-16 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-center text-3xl mb-4 text-indigo-400 shadow-inner">
                ✨
              </div>
              <h3 className="text-base font-semibold text-slate-200">No Review Generated Yet</h3>
              <p className="text-xs text-slate-400 max-w-sm mt-1 leading-relaxed">
                Paste your code snippet on the left and click{" "}
                <span className="text-indigo-300 font-medium">Run Review</span> to get an instant multi-agent analysis, vulnerability report, and refactored code.
              </p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
