import React, { useState } from 'react';
import { History, Search, Layers, Clock, ChevronRight, Calendar, ArrowUpRight } from 'lucide-react';
import { TaskSummary } from '../types';
import { formatDuration, formatDate } from '../utils/formatters';

interface HistoryPageProps {
  tasks: TaskSummary[];
  onSelectTask: (taskId: string) => void;
}

export const HistoryPage: React.FC<HistoryPageProps> = ({ tasks, onSelectTask }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredTasks = tasks.filter((t) =>
    t.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.user_prompt.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex-1 overflow-y-auto p-8 max-w-5xl mx-auto space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Task Execution History</h2>
          <p className="text-xs text-slate-400 mt-1">
            Browse and reopen completed multi-agent workflows, reviews, and artifacts.
          </p>
        </div>

        {/* Search Bar */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search past workflows..."
            className="w-full glass-input pl-9 pr-4 py-2 rounded-xl text-xs focus:outline-none"
          />
        </div>
      </div>

      {/* Task List */}
      {filteredTasks.length === 0 ? (
        <div className="glass-card p-12 rounded-3xl text-center text-slate-500 text-xs space-y-2">
          <History className="w-8 h-8 mx-auto text-slate-600" />
          <p>No historical task records match your criteria.</p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {filteredTasks.map((t) => (
            <div
              key={t.id}
              onClick={() => onSelectTask(t.id)}
              className="glass-card p-4 rounded-2xl flex items-center justify-between cursor-pointer hover:border-blue-500/40 hover:bg-slate-900/60 transition-all group"
            >
              <div className="flex items-center gap-3.5 min-w-0">
                <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700/60 text-blue-400 group-hover:scale-105 transition-transform flex-shrink-0">
                  <Layers className="w-5 h-5" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold text-slate-100 truncate group-hover:text-blue-400 transition-colors">
                      {t.title}
                    </h3>
                    {t.is_demo && (
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        DEMO
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 truncate max-w-xl mt-0.5">
                    {t.user_prompt}
                  </p>
                  <div className="flex items-center gap-3 text-[11px] text-slate-400 font-mono mt-1">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3 text-slate-500" />
                      {formatDate(t.created_at)}
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3 text-slate-500" />
                      {formatDuration(t.duration_seconds)}
                    </span>
                    <span>•</span>
                    <span className="text-slate-300 font-sans">{t.agents_count} agents</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 flex-shrink-0">
                <span className={`text-[10px] font-mono px-2.5 py-0.5 rounded-full border ${
                  t.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                  t.status === 'running' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                  'bg-rose-500/10 text-rose-400 border-rose-500/20'
                }`}>
                  {t.status.toUpperCase()}
                </span>
                <span className="text-blue-400 text-xs font-medium flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                  Reopen <ChevronRight className="w-4 h-4" />
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
