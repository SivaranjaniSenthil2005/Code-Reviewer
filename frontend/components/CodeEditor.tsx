"use client";

import React from "react";

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language?: string;
  placeholder?: string;
  disabled?: boolean;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  value,
  onChange,
  language = "python",
  placeholder = "Paste your code snippet here...",
  disabled = false,
}) => {
  const lineCount = Math.max(1, value.split("\n").length);

  return (
    <div className="relative flex border border-slate-700/80 rounded-xl bg-slate-950/90 backdrop-blur-md overflow-hidden shadow-2xl focus-within:ring-2 focus-within:ring-indigo-500/50 transition-all">
      {/* Line Numbers Gutter */}
      <div className="select-none py-3 px-3 bg-slate-900/60 border-r border-slate-800/80 text-right font-mono text-xs text-slate-500 min-w-[3rem]">
        {Array.from({ length: lineCount }).map((_, i) => (
          <div key={i + 1} className="leading-6">
            {i + 1}
          </div>
        ))}
      </div>

      {/* Editor Textarea */}
      <div className="relative flex-1">
        <textarea
          id="code-editor-input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          placeholder={placeholder}
          spellCheck={false}
          className="w-full h-80 p-3 bg-transparent font-mono text-sm text-slate-100 placeholder-slate-500 resize-y focus:outline-none leading-6 leading-relaxed selection:bg-indigo-500/30"
          style={{ tabSize: 4 }}
        />
        <div className="absolute top-2 right-3 px-2 py-0.5 rounded text-[10px] font-mono tracking-wider uppercase bg-slate-800/80 text-slate-400 border border-slate-700/50">
          {language}
        </div>
      </div>
    </div>
  );
};
