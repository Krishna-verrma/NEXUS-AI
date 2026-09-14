import React from 'react';
import { 
  PlusCircle, 
  LayoutDashboard, 
  Bot, 
  Files, 
  History, 
  FileText, 
  Settings, 
  Sparkles,
  Layers,
  Cpu
} from 'lucide-react';

export type NavPage = 'dashboard' | 'workspace' | 'agents' | 'files' | 'history' | 'reports' | 'settings';

interface SidebarProps {
  currentPage: NavPage;
  onNavigate: (page: NavPage) => void;
  onNewTask: () => void;
  isDemoMode: boolean;
  isConnected: boolean;
  activeTaskTitle?: string | null;
  onToggleDemoMode?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onNavigate,
  onNewTask,
  isDemoMode,
  isConnected,
  activeTaskTitle,
  onToggleDemoMode
}) => {
  const navItems: { id: NavPage; label: string; icon: React.ReactNode }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: 'workspace', label: 'Workspace', icon: <Layers className="w-4 h-4" /> },
    { id: 'agents', label: 'Agents', icon: <Bot className="w-4 h-4" /> },
    { id: 'files', label: 'Files', icon: <Files className="w-4 h-4" /> },
    { id: 'history', label: 'History', icon: <History className="w-4 h-4" /> },
    { id: 'reports', label: 'Reports', icon: <FileText className="w-4 h-4" /> },
    { id: 'settings', label: 'Settings', icon: <Settings className="w-4 h-4" /> },
  ];

  return (
    <aside className="w-64 bg-[#0a0d14] border-r border-slate-800/80 flex flex-col select-none z-20">
      {/* Brand Logo Header */}
      <div className="p-5 border-b border-slate-800/80 flex items-center gap-3">
        <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-600 shadow-lg shadow-blue-500/20">
          <Cpu className="w-5 h-5 text-white" />
          {/* Orbital nodes indicator */}
          <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-cyan-400 rounded-full ring-2 ring-[#0a0d14]"></span>
          <span className="absolute -bottom-0.5 -left-0.5 w-2 h-2 bg-purple-400 rounded-full ring-2 ring-[#0a0d14]"></span>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-extrabold text-base tracking-wider text-white font-mono">NEXUS AI</h1>
            <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded">
              v1.0
            </span>
          </div>
          <p className="text-[11px] text-slate-400 truncate max-w-[130px]">Multi-Agent Center</p>
        </div>
      </div>

      {/* New Task Button */}
      <div className="p-4">
        <button
          onClick={onNewTask}
          className="w-full flex items-center justify-between px-3.5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium text-sm rounded-xl shadow-lg shadow-blue-600/20 transition-all border border-blue-400/20 group"
        >
          <span className="flex items-center gap-2">
            <PlusCircle className="w-4 h-4 text-blue-200 group-hover:rotate-90 transition-transform duration-200" />
            New Task
          </span>
          <kbd className="text-[10px] px-1.5 py-0.5 bg-blue-700/60 rounded text-blue-200 font-mono">Ctrl+K</kbd>
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 space-y-1 overflow-y-auto">
        <div className="px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          Command
        </div>
        {navItems.map((item) => {
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <span className={isActive ? 'text-blue-400' : 'text-slate-400'}>
                {item.icon}
              </span>
              <span>{item.label}</span>
              {item.id === 'workspace' && activeTaskTitle && (
                <span className="ml-auto w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Connection & Status Footer */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-900/30 space-y-2">
        <button
          type="button"
          onClick={onToggleDemoMode}
          title="Click to toggle between Demo Mode and Live AI Mode"
          className="w-full flex items-center justify-between px-2.5 py-2 bg-slate-900/60 hover:bg-slate-800/80 rounded-xl border border-slate-800 transition-all cursor-pointer group"
        >
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${isDemoMode ? 'bg-amber-400 animate-pulse' : (isConnected ? 'bg-emerald-400' : 'bg-rose-400')}`}></span>
            <span className="text-xs font-medium text-slate-300 group-hover:text-white transition-colors">
              {isDemoMode ? 'Demo Mode' : (isConnected ? 'Live AI Active' : 'AI Offline')}
            </span>
          </div>
          <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded transition-colors ${
            isDemoMode
              ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
              : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
          }`}>
            {isDemoMode ? 'OFFLINE' : 'LIVE'}
          </span>
        </button>
        <div className="text-[10px] text-slate-500 text-center flex items-center justify-center gap-1">
          <Sparkles className="w-3 h-3 text-blue-400" />
          <span>Intelligent Workflow Engine</span>
        </div>
      </div>
    </aside>
  );
};
