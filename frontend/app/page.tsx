'use client';

import { useEffect, useState } from 'react';

export default function Home() {
  const [healthStatus, setHealthStatus] = useState<{
    status: string;
    loading: boolean;
    error: string | null;
  }>({
    status: '',
    loading: true,
    error: null,
  });

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await fetch(`${backendUrl}/health`);
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        const data = await res.json();
        setHealthStatus({ status: data.status, loading: false, error: null });
      } catch (err: any) {
        setHealthStatus({
          status: '',
          loading: false,
          error: err?.message || 'Failed to connect to backend',
        });
      }
    }
    checkHealth();
  }, [backendUrl]);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6">
      <div className="max-w-2xl w-full bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-2xl space-y-6">
        <div className="flex items-center space-x-3">
          <div className="h-3 w-3 rounded-full bg-emerald-500 animate-ping" />
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            AI Code Review & Refactoring Platform
          </h1>
        </div>
        <p className="text-slate-400 text-sm leading-relaxed">
          Monorepo foundation configured with Next.js 15 (Frontend) and FastAPI (Backend).
        </p>

        <div className="border border-slate-800 bg-slate-950/60 rounded-lg p-5 space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400 font-medium">FastAPI Backend Target:</span>
            <code className="text-indigo-300 bg-indigo-950/50 px-2 py-1 rounded border border-indigo-900/50 text-xs">
              {backendUrl}/health
            </code>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400 font-medium">Backend Health Status:</span>
            {healthStatus.loading ? (
              <span className="text-amber-400 text-xs animate-pulse">Checking status...</span>
            ) : healthStatus.error ? (
              <span className="text-rose-400 text-xs font-semibold px-2.5 py-1 bg-rose-950/50 border border-rose-900/50 rounded">
                Disconnected ({healthStatus.error})
              </span>
            ) : (
              <span className="text-emerald-400 text-xs font-semibold px-2.5 py-1 bg-emerald-950/50 border border-emerald-900/50 rounded flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                Connected ({healthStatus.status})
              </span>
            )}
          </div>
        </div>

        <div className="text-xs text-slate-500 text-center pt-2">
          Phase 1 Monorepo Infrastructure initialized successfully.
        </div>
      </div>
    </main>
  );
}
