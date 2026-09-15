"use client";

import React, { useState } from "react";
import { ReviewData } from "./ReviewPanel";
import { downloadMarkdownReport } from "@/lib/markdown-export";

interface ExportButtonProps {
  data: ReviewData;
  originalCode: string;
}

export const ExportButton: React.FC<ExportButtonProps> = ({ data, originalCode }) => {
  const [downloaded, setDownloaded] = useState(false);

  const handleDownload = () => {
    downloadMarkdownReport(data, originalCode);
    setDownloaded(true);
    setTimeout(() => setDownloaded(false), 2000);
  };

  return (
    <button
      id="export-markdown-btn"
      type="button"
      onClick={handleDownload}
      className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 shadow-sm transition-all active:scale-95"
    >
      <span>{downloaded ? "✅" : "📥"}</span>
      <span>{downloaded ? "Downloaded!" : "Export Markdown"}</span>
    </button>
  );
};
