import React, { useState } from 'react';
import {
  Search,
  FileSearch,
  Globe2,
  Terminal,
  FileText,
  CalendarCheck,
  Monitor,
  Sparkles,
  ArrowRight,
  Shield,
  Activity,
  CheckCircle2,
} from 'lucide-react';

interface HomeProps {
  onQuickAction: (prompt: string, targetAgent?: string) => void;
  onNavigate: (page: string) => void;
}

export const Home: React.FC<HomeProps> = ({ onQuickAction, onNavigate }) => {
  const [commandInput, setCommandInput] = useState('');

  const handleCommandSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!commandInput.trim()) return;
    onQuickAction(commandInput.trim());
  };

  const quickActions = [
    {
      title: 'Analyze File',
      icon: FileSearch,
      desc: 'Deep inspection, tokens & syntax',
      agent: 'file_agent',
      prompt: 'Search and inspect files in the workspace directory',
      color: 'from-blue-500/20 to-cyan-500/10 text-blue-400 border-blue-500/30',
    },
    {
      title: 'Search Web',
      icon: Globe2,
      desc: 'Live query & technical synthesis',
      agent: 'web_agent',
      prompt: 'Search web for latest breakthroughs in AI agent orchestration',
      color: 'from-emerald-500/20 to-teal-500/10 text-emerald-400 border-emerald-500/30',
    },
    {
      title: 'Write Code',
      icon: Terminal,
      desc: 'Algorithms, tests & sandboxes',
      agent: 'coding_agent',
      prompt: 'Write a python async generator with unit test benchmark',
      color: 'from-pink-500/20 to-rose-500/10 text-pink-400 border-pink-500/30',
    },
    {
      title: 'Create Document',
      icon: FileText,
      desc: 'Technical specs & whitepapers',
      agent: 'creative_agent',
      prompt: 'Generate an executive vision document for Nexus AI',
      color: 'from-purple-500/20 to-indigo-500/10 text-purple-400 border-purple-500/30',
    },
    {
      title: 'Schedule Event',
      icon: CalendarCheck,
      desc: 'Agenda & meeting orchestration',
      agent: 'productivity_agent',
      prompt: 'Schedule Sprint Architecture Review for 15:00 today',
      color: 'from-amber-500/20 to-yellow-500/10 text-amber-400 border-amber-500/30',
    },
    {
      title: 'Control Computer',
      icon: Monitor,
      desc: 'Launch apps & capture screen',
      agent: 'computer_agent',
      prompt: 'Launch notepad and capture current desktop status',
      color: 'from-violet-500/20 to-fuchsia-500/10 text-violet-400 border-violet-500/30',
    },
  ];

  return (
    <div className="h-full overflow-y-auto px-8 py-10 cyber-radial-bg space-y-12">
      {/* Hero Section */}
      <div className="max-w-4xl mx-auto text-center space-y-4">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1 rounded-full bg-nexus-cyan/10 border border-nexus-cyan/30 text-nexus-cyan text-xs font-semibold tracking-wider">
          <Sparkles className="w-3.5 h-3.5 animate-spin" />
          <span>AUTONOMOUS MULTI-AGENT RUNTIME</span>
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white">
          NEXUS <span className="text-transparent bg-clip-text bg-gradient-to-r from-nexus-cyan via-indigo-400 to-nexus-violet">AI</span>
        </h1>

        <p className="text-lg text-slate-400 max-w-xl mx-auto font-light">
          Your intelligent operating layer.
        </p>

        {/* Large Command Box */}
        <form onSubmit={handleCommandSubmit} className="relative max-w-2xl mx-auto pt-4">
          <div className="relative flex items-center shadow-cyan-glow rounded-2xl overflow-hidden border border-nexus-cyan/40 bg-nexus-surface/90 backdrop-blur-xl">
            <Search className="w-5 h-5 text-nexus-cyan ml-5 shrink-0" />
            <input
              type="text"
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              placeholder="Ask Nexus anything..."
              className="w-full bg-transparent px-4 py-4 text-base text-white placeholder-slate-500 focus:outline-none"
            />
            <button
              type="submit"
              className="mr-3 px-5 py-2.5 rounded-xl bg-gradient-to-r from-nexus-cyan to-nexus-indigo hover:from-cyan-400 hover:to-indigo-500 text-slate-950 font-bold text-xs tracking-wider uppercase transition-all shadow-md shrink-0 flex items-center space-x-1.5"
            >
              <span>Dispatch</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </form>
      </div>

      {/* Quick Action Matrix */}
      <div className="max-w-5xl mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">
            Rapid Execution Pipelines
          </h2>
          <span className="text-xs text-slate-500">Click to run immediately</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {quickActions.map((action, idx) => {
            const Icon = action.icon;
            return (
              <div
                key={idx}
                onClick={() => onQuickAction(action.prompt, action.agent)}
                className={`glass-panel glass-panel-hover p-4 rounded-xl cursor-pointer border bg-gradient-to-br ${action.color} group relative overflow-hidden`}
              >
                <div className="flex items-start justify-between">
                  <div className="p-2.5 rounded-lg bg-nexus-bg/70 border border-nexus-border">
                    <Icon className="w-5 h-5" />
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-white group-hover:translate-x-1 transition-all" />
                </div>
                <div className="mt-4">
                  <h3 className="text-sm font-semibold text-white tracking-wide group-hover:text-nexus-cyan transition-colors">
                    {action.title}
                  </h3>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                    {action.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* System Telemetry & Status Matrix */}
      <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
        <div className="glass-panel p-4 rounded-xl border border-nexus-border space-y-2">
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400">
            <Shield className="w-4 h-4 text-nexus-emerald" />
            <span>SECURITY ISOLATION</span>
          </div>
          <div className="text-2xl font-bold text-white">Active Guardrails</div>
          <p className="text-xs text-slate-400">
            Destructive actions require interactive human-in-the-loop permission.
          </p>
        </div>

        <div
          onClick={() => onNavigate('agents')}
          className="glass-panel glass-panel-hover p-4 rounded-xl border border-nexus-border space-y-2 cursor-pointer"
        >
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400">
            <Activity className="w-4 h-4 text-nexus-cyan" />
            <span>AGENT HIVE</span>
          </div>
          <div className="text-2xl font-bold text-white">9 Autonomous Units</div>
          <p className="text-xs text-slate-400">
            Specialized in Computer, Files, Web, Code, Productivity, Comms, Data, and Creative.
          </p>
        </div>

        <div
          onClick={() => onNavigate('tasks')}
          className="glass-panel glass-panel-hover p-4 rounded-xl border border-nexus-border space-y-2 cursor-pointer"
        >
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400">
            <CheckCircle2 className="w-4 h-4 text-nexus-violet" />
            <span>BACKGROUND ENGINE</span>
          </div>
          <div className="text-2xl font-bold text-white">Zero Overhead</div>
          <p className="text-xs text-slate-400">
            Asynchronous task queue with live progress streaming via WebSockets.
          </p>
        </div>
      </div>
    </div>
  );
};
