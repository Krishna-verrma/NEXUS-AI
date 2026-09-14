import React from 'react';
import { X, Wrench, Shield, Zap, Terminal } from 'lucide-react';
import { AgentDescriptorData } from '../../services/agentApi';

interface AgentDetailsProps {
  agent: AgentDescriptorData | null;
  onClose: () => void;
  onRun: (agentRole: string) => void;
}

export const AgentDetails: React.FC<AgentDetailsProps> = ({ agent, onClose, onRun }) => {
  if (!agent) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="glass-panel w-full max-w-xl rounded-2xl border border-nexus-cyan/40 shadow-cyan-glow p-6 space-y-6 relative animate-in fade-in zoom-in-95 duration-200">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg bg-nexus-surface hover:bg-nexus-card text-slate-400 hover:text-white transition-colors border border-nexus-border"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header */}
        <div className="flex items-center space-x-3">
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center border text-lg font-bold"
            style={{
              backgroundColor: `${agent.color}20`,
              borderColor: `${agent.color}50`,
              color: agent.color,
            }}
          >
            {agent.name.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <h2 className="text-lg font-bold text-white tracking-wide">
              {agent.name}
            </h2>
            <div className="flex items-center space-x-2 text-xs text-slate-400 font-mono">
              <span>role: {agent.role}</span>
              <span>•</span>
              <span className="text-nexus-emerald">Status: {agent.status.toUpperCase()}</span>
            </div>
          </div>
        </div>

        {/* Description */}
        <div className="p-3.5 rounded-xl bg-nexus-surface/60 border border-nexus-border text-sm text-slate-300 leading-relaxed">
          {agent.description}
        </div>

        {/* Capabilities Grid */}
        <div className="space-y-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
            <Zap className="w-3.5 h-3.5 text-nexus-cyan" />
            <span>Autonomous Capabilities</span>
          </h4>
          <div className="grid grid-cols-2 gap-2">
            {agent.capabilities.map((cap, idx) => (
              <div
                key={idx}
                className="p-2.5 rounded-lg bg-nexus-card border border-nexus-border text-xs text-slate-200 font-medium"
              >
                {cap}
              </div>
            ))}
          </div>
        </div>

        {/* Tool Bindings */}
        <div className="space-y-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
            <Wrench className="w-3.5 h-3.5 text-nexus-violet" />
            <span>Allowed Tool Bindings</span>
          </h4>
          <div className="flex flex-wrap gap-2">
            {agent.tools.map((t, idx) => (
              <span
                key={idx}
                className="text-xs font-mono px-2.5 py-1 rounded-md bg-nexus-surface border border-nexus-border text-nexus-cyan"
              >
                {t}
              </span>
            ))}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="pt-4 border-t border-nexus-border flex items-center justify-between">
          <span className="text-xs font-mono text-slate-500">
            Total Telemetry Executions: <strong>{agent.totalExecutions}</strong>
          </span>
          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-nexus-surface hover:bg-nexus-card text-slate-300 border border-nexus-border text-xs font-semibold"
            >
              Dismiss
            </button>
            <button
              onClick={() => {
                onClose();
                onRun(agent.role);
              }}
              className="px-5 py-2 rounded-xl bg-gradient-to-r from-nexus-cyan to-nexus-indigo text-slate-950 text-xs font-bold shadow-cyan-glow"
            >
              Direct Dispatch
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
