import React from 'react';
import { ArrowDown, CheckCircle, Clock, Wrench, ShieldAlert } from 'lucide-react';

export interface ActivityTrace {
  agentRole: string;
  action: string;
  status: 'started' | 'step' | 'tool_call' | 'finished';
  timestamp: string;
  detail?: string;
  toolCalls?: Array<{
    toolName: string;
    parameters: Record<string, any>;
    status: string;
    result?: any;
  }>;
}

interface AgentActivityProps {
  traces: ActivityTrace[];
}

export const AgentActivity: React.FC<AgentActivityProps> = ({ traces }) => {
  if (!traces || traces.length === 0) return null;

  return (
    <div className="my-3 p-3.5 rounded-xl bg-nexus-surface/90 border border-nexus-border/80 shadow-sm space-y-2">
      <div className="flex items-center space-x-2 text-[11px] font-bold tracking-wider text-slate-400 uppercase">
        <Clock className="w-3.5 h-3.5 text-nexus-cyan" />
        <span>Agent Reasoning Pipeline & Telemetry</span>
      </div>

      <div className="space-y-2 pt-1">
        {traces.map((trace, idx) => {
          const isLast = idx === traces.length - 1;
          const isFinished = trace.status === 'finished';

          return (
            <div key={idx} className="relative">
              <div className="flex items-start space-x-2.5">
                {/* Node Status Dot */}
                <div className="mt-1">
                  {isFinished ? (
                    <div className="w-4 h-4 rounded-full bg-nexus-emerald/20 border border-nexus-emerald flex items-center justify-center text-nexus-emerald">
                      <CheckCircle className="w-2.5 h-2.5" />
                    </div>
                  ) : trace.status === 'tool_call' ? (
                    <div className="w-4 h-4 rounded-full bg-nexus-violet/20 border border-nexus-violet flex items-center justify-center text-nexus-violet">
                      <Wrench className="w-2.5 h-2.5" />
                    </div>
                  ) : (
                    <div className="w-4 h-4 rounded-full bg-nexus-cyan/20 border border-nexus-cyan flex items-center justify-center text-nexus-cyan">
                      <div className="w-1.5 h-1.5 rounded-full bg-nexus-cyan animate-ping" />
                    </div>
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-semibold text-slate-200">
                      {trace.action}
                    </span>
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-nexus-bg text-slate-400 border border-nexus-border">
                      {trace.agentRole}
                    </span>
                  </div>

                  {trace.detail && (
                    <p className="text-[11px] text-slate-400 font-mono leading-tight">
                      {trace.detail}
                    </p>
                  )}

                  {/* Tool Calls if any */}
                  {trace.toolCalls && trace.toolCalls.length > 0 && (
                    <div className="mt-1.5 space-y-1 pl-2 border-l border-nexus-violet/40">
                      {trace.toolCalls.map((tc, tcIdx) => (
                        <div key={tcIdx} className="text-[11px] font-mono text-slate-300 flex items-center space-x-1.5">
                          <Wrench className="w-3 h-3 text-nexus-violet shrink-0" />
                          <span>tool: <code className="text-nexus-cyan">{tc.toolName}</code></span>
                          <span className={`text-[10px] px-1 rounded ${tc.status === 'success' ? 'bg-nexus-emerald/20 text-nexus-emerald' : 'bg-nexus-rose/20 text-nexus-rose'}`}>
                            {tc.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Vertical connector line */}
              {!isLast && (
                <div className="ml-2 my-0.5 w-[1px] h-3 bg-nexus-border flex items-center justify-center">
                  <ArrowDown className="w-2.5 h-2.5 text-slate-600" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
