import React, { useState, useEffect } from 'react';
import { Cpu, ShieldCheck, Wifi, WifiOff, Sparkles, Terminal, Activity, Bell } from 'lucide-react';
import { wsService } from '../services/websocketService';
import { request } from '../services/api';

interface NavbarProps {
  activePage: string;
  onNavigate: (page: string) => void;
  pendingTicketCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({ activePage, onNavigate, pendingTicketCount }) => {
  const [wsConnected, setWsConnected] = useState(wsService.getConnected());
  const [vitals, setVitals] = useState({ cpu: 14.5, mem: 41.2, isDemo: true });
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const unsub = wsService.subscribe('status', (data) => {
      setWsConnected(data.connected);
    });

    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    }, 1000);

    // Fetch vitals
    const fetchVitals = async () => {
      try {
        const res = await request<any>('/api/system/vitals');
        setVitals({
          cpu: res.cpuUsagePercent,
          mem: res.memoryUsagePercent,
          isDemo: res.isDemoMode
        });
      } catch {
        // use default
      }
    };
    fetchVitals();
    const vitalsInterval = setInterval(fetchVitals, 10000);

    return () => {
      unsub();
      clearInterval(timer);
      clearInterval(vitalsInterval);
    };
  }, []);

  return (
    <header className="h-16 border-b border-nexus-border bg-nexus-surface/80 backdrop-blur-md px-6 flex items-center justify-between z-30 select-none">
      {/* Brand */}
      <div className="flex items-center space-x-3 cursor-pointer" onClick={() => onNavigate('home')}>
        <div className="relative flex items-center justify-center w-9 h-9 rounded-lg bg-nexus-card border border-nexus-cyan/40 shadow-cyan-glow">
          <div className="absolute inset-0 rounded-lg bg-gradient-to-br from-nexus-cyan/20 to-nexus-violet/20 animate-pulse" />
          <Terminal className="w-5 h-5 text-nexus-cyan relative z-10" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-bold tracking-wider text-white text-base">NEXUS</span>
            <span className="font-extrabold text-nexus-cyan text-sm tracking-widest px-1.5 py-0.5 rounded bg-nexus-cyan/10 border border-nexus-cyan/30">AI</span>
          </div>
          <span className="text-[10px] tracking-widest text-slate-400 uppercase">Intelligent Operating Layer</span>
        </div>
      </div>

      {/* Center Status Indicators */}
      <div className="hidden md:flex items-center space-x-4">
        {/* Demo Mode Badge */}
        {vitals.isDemo ? (
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-nexus-amber/10 border border-nexus-amber/40 text-nexus-amber text-xs font-medium">
            <Sparkles className="w-3.5 h-3.5 animate-spin" />
            <span className="tracking-wide">DEMO MODE ACTIVE</span>
          </div>
        ) : (
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-nexus-emerald/10 border border-nexus-emerald/40 text-nexus-emerald text-xs font-medium">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span className="tracking-wide">ENTERPRISE CLOUD</span>
          </div>
        )}

        {/* Hardware Vitals */}
        <div className="flex items-center space-x-3 px-3 py-1 rounded-lg bg-nexus-card/60 border border-nexus-border text-xs text-slate-300">
          <div className="flex items-center space-x-1.5">
            <Cpu className="w-3.5 h-3.5 text-nexus-cyan" />
            <span>CPU <strong className="text-white">{vitals.cpu}%</strong></span>
          </div>
          <span className="text-slate-600">|</span>
          <div className="flex items-center space-x-1.5">
            <Activity className="w-3.5 h-3.5 text-nexus-violet" />
            <span>RAM <strong className="text-white">{vitals.mem}%</strong></span>
          </div>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-3">
        {/* Security Alert Badge */}
        {pendingTicketCount > 0 && (
          <button
            onClick={() => onNavigate('chat')}
            className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-nexus-rose/20 border border-nexus-rose text-nexus-rose text-xs font-semibold animate-bounce"
          >
            <Bell className="w-3.5 h-3.5" />
            <span>{pendingTicketCount} Pending Approval</span>
          </button>
        )}

        {/* WebSocket Status */}
        <div
          className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-mono border ${
            wsConnected
              ? 'bg-nexus-emerald/10 border-nexus-emerald/40 text-nexus-emerald'
              : 'bg-nexus-rose/10 border-nexus-rose/40 text-nexus-rose'
          }`}
        >
          {wsConnected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
          <span>{wsConnected ? 'LIVE STREAM' : 'OFFLINE'}</span>
        </div>

        {/* Clock */}
        <div className="hidden lg:block text-xs font-mono text-slate-400 px-2 py-1 bg-nexus-card rounded border border-nexus-border">
          {currentTime}
        </div>
      </div>
    </header>
  );
};
