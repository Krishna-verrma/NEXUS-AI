import React from 'react';
import {
  BrainCircuit,
  Monitor,
  FolderGit2,
  Globe2,
  Terminal,
  CalendarCheck,
  MessageSquareShare,
  BarChart3,
  Sparkles,
  ArrowUpRight,
  Shield,
  CheckCircle2,
} from 'lucide-react';
import { AgentDescriptorData } from '../../services/agentApi';

const AVATAR_MAP: Record<string, any> = {
  BrainCircuit,
  Monitor,
  FolderGit2,
  Globe2,
  Terminal,
  CalendarCheck,
  MessageSquareShare,
  BarChart3,
  Sparkles,
};

interface AgentCardProps {
  agent: AgentDescriptorData;
  onSelect: (agent: AgentDescriptorData) => void;
  onRunDirect: (agentRole: string) => void;
}

export const AgentCard: React.FC<AgentCardProps> = ({ agent, onSelect, onRunDirect }) => {
  const Icon = AVATAR_MAP[agent.avatar] || Sparkles;

  return (
    <div className="glass-panel glass-panel-hover p-5 rounded-2xl border border-nexus-border flex flex-col justify-between group relative overflow-hidden">
      {/* Accent Glow Top Border */}
      <div
        className="absolute top-0 left-0 right-0 h-[2px]"
        style={{ backgroundColor: agent.color }}
      />

      <div className="space-y-4">
        {/* Header with Avatar & Status */}
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center border transition-transform group-hover:scale-105"
              style={{
                backgroundColor: `${agent.color}15`,
                borderColor: `${agent.color}40`,
                color: agent.color,
              }}
            >
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white tracking-wide">
                {agent.name}
              </h3>
              <span className="text-[10px] font-mono text-slate-400">
                {agent.role}
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-nexus-emerald/10 border border-nexus-emerald/30 text-nexus-emerald text-[10px] font-mono">
            <div className="w-1.5 h-1.5 rounded-full bg-nexus-emerald animate-pulse" />
            <span>IDLE</span>
          </div>
        </div>

        {/* Description */}
        <p className="text-xs text-slate-300 leading-relaxed font-normal">
          {agent.description}
        </p>

        {/* Capabilities Chips */}
        <div className="space-y-1.5 pt-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
            Capabilities
          </span>
          <div className="flex flex-wrap gap-1.5">
            {agent.capabilities.map((cap, idx) => (
              <span
                key={idx}
                className="text-[10px] px-2 py-0.5 rounded-md bg-nexus-card border border-nexus-border text-slate-300 font-medium"
              >
                {cap}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Footer controls */}
      <div className="mt-5 pt-4 border-t border-nexus-border/60 flex items-center justify-between text-xs">
        <span className="text-[11px] font-mono text-slate-500">
          Executions: <strong className="text-slate-300">{agent.totalExecutions}</strong>
        </span>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => onSelect(agent)}
            className="px-2.5 py-1 rounded-lg bg-nexus-surface hover:bg-nexus-card text-slate-300 hover:text-white border border-nexus-border transition-colors text-xs"
          >
            Inspect
          </button>
          <button
            onClick={() => onRunDirect(agent.role)}
            className="px-3 py-1 rounded-lg bg-nexus-cyan/15 hover:bg-nexus-cyan/25 text-nexus-cyan border border-nexus-cyan/30 text-xs font-semibold flex items-center space-x-1 transition-all"
          >
            <span>Run</span>
            <ArrowUpRight className="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>
  );
};
