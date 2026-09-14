import React from 'react';
import {
  LayoutDashboard,
  MessageSquare,
  Bot,
  ListTodo,
  FolderTree,
  Zap,
  Calendar,
  History,
  Settings,
  ShieldAlert,
} from 'lucide-react';

interface SidebarProps {
  activePage: string;
  onNavigate: (page: string) => void;
  pendingTicketCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ activePage, onNavigate, pendingTicketCount }) => {
  const navItems = [
    { id: 'home', label: 'HOME', icon: LayoutDashboard },
    { id: 'chat', label: 'CHAT', icon: MessageSquare, badge: pendingTicketCount > 0 ? pendingTicketCount : undefined },
    { id: 'agents', label: 'AGENTS', icon: Bot, highlight: '9 units' },
    { id: 'tasks', label: 'TASKS', icon: ListTodo },
    { id: 'files', label: 'FILES', icon: FolderTree },
    { id: 'automations', label: 'AUTOMATIONS', icon: Zap },
    { id: 'calendar', label: 'CALENDAR', icon: Calendar },
    { id: 'activity', label: 'ACTIVITY', icon: History },
    { id: 'settings', label: 'SETTINGS', icon: Settings },
  ];

  return (
    <aside className="w-64 border-r border-nexus-border bg-nexus-surface/50 backdrop-blur-md flex flex-col justify-between p-4 select-none shrink-0">
      <div className="space-y-1">
        <div className="px-3 py-2 text-[11px] font-semibold text-slate-500 tracking-wider uppercase">
          Command Matrix
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium tracking-wide transition-all ${
                isActive
                  ? 'bg-nexus-cyan/15 text-nexus-cyan border border-nexus-cyan/40 shadow-cyan-glow font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-nexus-hover border border-transparent'
              }`}
            >
              <div className="flex items-center space-x-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-nexus-cyan' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge !== undefined && (
                <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-nexus-rose text-white font-bold">
                  {item.badge}
                </span>
              )}
              {item.highlight && !isActive && (
                <span className="text-[10px] text-slate-500 font-mono">
                  {item.highlight}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Footer System Status Card */}
      <div className="p-3 rounded-xl bg-nexus-card/60 border border-nexus-border space-y-2">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-nexus-cyan animate-ping" />
          <span className="text-xs font-medium text-slate-300">Hive Active</span>
        </div>
        <p className="text-[11px] text-slate-500 leading-relaxed">
          Nexus Orchestrator delegating across 9 isolated agents.
        </p>
      </div>
    </aside>
  );
};
