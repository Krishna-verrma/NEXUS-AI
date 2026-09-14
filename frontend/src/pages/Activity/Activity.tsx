import React, { useState } from 'react';
import { History, Shield, Wrench, CheckCircle2, AlertTriangle, Filter } from 'lucide-react';

interface AuditItem {
  id: string;
  timestamp: string;
  agentRole: string;
  operation: string;
  status: 'success' | 'security_gate' | 'running';
  details: string;
  durationMs: number;
}

export const Activity: React.FC = () => {
  const [filterAgent, setFilterAgent] = useState('all');

  const [logs] = useState<AuditItem[]>([
    {
      id: 'log-1',
      timestamp: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
      agentRole: 'file_agent',
      operation: 'search_files',
      status: 'success',
      details: 'Discovered 42 matching files in workspace root',
      durationMs: 14.2,
    },
    {
      id: 'log-2',
      timestamp: new Date(Date.now() - 1000 * 60 * 8).toISOString(),
      agentRole: 'coding_agent',
      operation: 'analyze_code_structure',
      status: 'success',
      details: 'Inspected Python AST: verified 12 functions, 0 fatal syntax errors',
      durationMs: 28.5,
    },
    {
      id: 'log-3',
      timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
      agentRole: 'file_agent',
      operation: 'delete_file',
      status: 'security_gate',
      details: 'Human-in-the-loop authorization requested for cache deletion',
      durationMs: 0.0,
    },
    {
      id: 'log-4',
      timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
      agentRole: 'computer_agent',
      operation: 'launch_app',
      status: 'success',
      details: 'Started process calc.exe via Windows subsystem',
      durationMs: 120.0,
    },
    {
      id: 'log-5',
      timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
      agentRole: 'web_agent',
      operation: 'search_web',
      status: 'success',
      details: 'Aggregated 3 authoritative sources for multi-agent architecture',
      durationMs: 98.4,
    },
  ]);

  const filtered = filterAgent === 'all' ? logs : logs.filter((l) => l.agentRole === filterAgent);

  return (
    <div className="h-full overflow-y-auto px-8 py-8 space-y-8 bg-nexus-bg">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-nexus-border pb-6">
        <div>
          <div className="flex items-center space-x-2">
            <History className="w-5 h-5 text-nexus-cyan" />
            <h1 className="text-2xl font-extrabold text-white tracking-tight">
              Audit & Activity Stream
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time telemetry of agent decisions, tool execution latency, and security authorizations.
          </p>
        </div>

        {/* Filter */}
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-slate-500" />
          <select
            value={filterAgent}
            onChange={(e) => setFilterAgent(e.target.value)}
            className="bg-nexus-card border border-nexus-border text-xs rounded-xl px-3 py-1.5 text-slate-300 focus:outline-none focus:border-nexus-cyan"
          >
            <option value="all">All Agents</option>
            <option value="file_agent">File Agent</option>
            <option value="coding_agent">Coding Agent</option>
            <option value="computer_agent">Computer Agent</option>
            <option value="web_agent">Web Agent</option>
          </select>
        </div>
      </div>

      {/* Log Feed */}
      <div className="space-y-3 max-w-5xl">
        {filtered.map((log) => (
          <div
            key={log.id}
            className="glass-panel p-4 rounded-xl border border-nexus-border flex flex-col sm:flex-row sm:items-center justify-between gap-3"
          >
            <div className="flex items-start space-x-3.5">
              <div className="p-2 rounded-xl bg-nexus-card border border-nexus-border text-slate-400 mt-0.5">
                {log.status === 'security_gate' ? (
                  <AlertTriangle className="w-4 h-4 text-nexus-amber" />
                ) : (
                  <Wrench className="w-4 h-4 text-nexus-cyan" />
                )}
              </div>
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-bold text-white font-mono">{log.operation}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-nexus-surface border border-nexus-border text-slate-400">
                    {log.agentRole}
                  </span>
                </div>
                <p className="text-xs text-slate-400">{log.details}</p>
              </div>
            </div>

            <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center shrink-0 text-right">
              <span className={`text-[10px] font-mono font-bold uppercase ${
                log.status === 'security_gate' ? 'text-nexus-amber' : 'text-nexus-emerald'
              }`}>
                {log.status === 'security_gate' ? 'GATE TRIGGERED' : 'SUCCESS'}
              </span>
              <div className="flex items-center space-x-2 text-[11px] font-mono text-slate-500">
                <span>{log.durationMs}ms</span>
                <span>•</span>
                <span>{new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
