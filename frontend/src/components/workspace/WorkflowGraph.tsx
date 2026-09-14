import React from 'react';
import { 
  ArrowDown, 
  CheckCircle2, 
  Clock, 
  Loader2, 
  Sparkles, 
  User, 
  FileSpreadsheet,
  Brain, 
  Bot,
  AlertTriangle
} from 'lucide-react';
import { TaskStep } from '../../types';

interface WorkflowGraphProps {
  userPrompt: string;
  steps: TaskStep[];
  onSelectStep: (step: TaskStep) => void;
  selectedStepId?: string | null;
}

export const WorkflowGraph: React.FC<WorkflowGraphProps> = ({
  userPrompt,
  steps,
  onSelectStep,
  selectedStepId
}) => {
  return (
    <div className="flex flex-col items-center gap-3 py-6 px-4 max-w-2xl mx-auto select-none">
      {/* 1. User Request Node */}
      <div className="w-full max-w-md p-3.5 rounded-xl bg-slate-900/80 border border-slate-700/80 shadow-md flex items-center gap-3">
        <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
          <User className="w-4 h-4" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-mono uppercase text-slate-500 font-semibold">User Goal</div>
          <div className="text-xs font-medium text-slate-200 truncate">{userPrompt}</div>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full">
          Received
        </span>
      </div>

      {/* Down Connector */}
      <div className="flex items-center justify-center text-slate-600">
        <ArrowDown className="w-4 h-4" />
      </div>

      {/* 2. Nexus Orchestrator Node */}
      <div className="w-full max-w-md p-3.5 rounded-xl bg-gradient-to-r from-blue-950/40 via-indigo-950/40 to-slate-900/80 border border-indigo-500/30 shadow-lg flex items-center gap-3">
        <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
          <Brain className="w-4 h-4" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-mono uppercase text-indigo-400 font-semibold">Central Engine</div>
          <div className="text-xs font-semibold text-slate-100">Nexus Orchestrator</div>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded-full flex items-center gap-1">
          <Sparkles className="w-2.5 h-2.5" /> Coordinated
        </span>
      </div>

      {/* Down Connector */}
      <div className="flex items-center justify-center text-slate-600">
        <ArrowDown className="w-4 h-4" />
      </div>

      {/* 3. Specialized Agents Cluster */}
      <div className="w-full max-w-lg p-4 rounded-2xl bg-[#0a0e17] border border-slate-800 shadow-inner">
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800 text-xs">
          <span className="font-mono text-[11px] text-slate-400 flex items-center gap-1.5 uppercase font-semibold">
            <Bot className="w-3.5 h-3.5 text-cyan-400" />
            Specialized Agent Execution Pipeline
          </span>
          <span className="text-[10px] font-mono text-slate-500">{steps.length} Nodes</span>
        </div>

        <div className="space-y-2">
          {steps.map((step) => {
            const isSelected = selectedStepId === step.id;
            const isRunning = step.status === 'running';
            const isCompleted = step.status === 'completed';

            return (
              <div
                key={step.id}
                onClick={() => onSelectStep(step)}
                className={`flex items-center justify-between p-2.5 rounded-xl border cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-blue-600/15 border-blue-500/50 shadow-md ring-1 ring-blue-500/30'
                    : isRunning
                    ? 'bg-blue-950/20 border-blue-500/40 animate-pulse'
                    : 'bg-slate-900/50 border-slate-800/80 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <span className="text-[11px] font-mono text-slate-500 w-4">
                    {step.step_order}
                  </span>
                  <span className="text-xs font-medium text-slate-200">
                    {step.agent_name}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {step.status === 'completed' && (
                    <span className="text-[10px] font-medium text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Done
                    </span>
                  )}
                  {step.status === 'running' && (
                    <span className="text-[10px] font-medium text-blue-400 flex items-center gap-1">
                      <Loader2 className="w-3 h-3 animate-spin" /> Active
                    </span>
                  )}
                  {step.status === 'waiting' && (
                    <span className="text-[10px] font-medium text-slate-500 flex items-center gap-1">
                      <Clock className="w-3 h-3" /> Queued
                    </span>
                  )}
                  {step.status === 'needs_review' && (
                    <span className="text-[10px] font-medium text-amber-400 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" /> Revision
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Down Connector */}
      <div className="flex items-center justify-center text-slate-600">
        <ArrowDown className="w-4 h-4" />
      </div>

      {/* 4. Final Result / Strategic Output Node */}
      <div className="w-full max-w-md p-3.5 rounded-xl bg-gradient-to-r from-emerald-950/30 to-blue-950/30 border border-emerald-500/30 shadow-lg flex items-center gap-3">
        <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
          <FileSpreadsheet className="w-4 h-4" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-mono uppercase text-emerald-400 font-semibold">Deliverable</div>
          <div className="text-xs font-semibold text-slate-100">Approved Strategic Solution</div>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-full">
          Finalized
        </span>
      </div>
    </div>
  );
};
