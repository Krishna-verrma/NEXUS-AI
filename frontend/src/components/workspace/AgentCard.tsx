import React from 'react';
import { 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  Loader2, 
  RotateCw, 
  ChevronRight, 
  Brain, 
  Search, 
  Code2, 
  BarChart3, 
  FileText, 
  AlertTriangle, 
  FileSpreadsheet 
} from 'lucide-react';
import { TaskStep, StepStatus } from '../../types';
import { formatDuration } from '../../utils/formatters';

interface AgentCardProps {
  step: TaskStep;
  onClick: () => void;
}

const getAgentIcon = (agentId: string) => {
  switch (agentId) {
    case 'orchestrator': return <Brain className="w-5 h-5 text-indigo-400" />;
    case 'data_analyst': return <BarChart3 className="w-5 h-5 text-blue-400" />;
    case 'research': return <Search className="w-5 h-5 text-cyan-400" />;
    case 'coding': return <Code2 className="w-5 h-5 text-emerald-400" />;
    case 'document': return <FileText className="w-5 h-5 text-purple-400" />;
    case 'risk': return <AlertTriangle className="w-5 h-5 text-amber-400" />;
    case 'reviewer': return <CheckCircle2 className="w-5 h-5 text-teal-400" />;
    case 'report': return <FileSpreadsheet className="w-5 h-5 text-rose-400" />;
    case 'schedule': return <Clock className="w-5 h-5 text-amber-400" />;
    default: return <Brain className="w-5 h-5 text-blue-400" />;
  }
};

const getStatusBadge = (status: StepStatus) => {
  switch (status) {
    case 'waiting':
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded-full border border-slate-700/60">
          <Clock className="w-3 h-3" /> Waiting
        </span>
      );
    case 'planning':
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-indigo-300 bg-indigo-500/10 px-2 py-0.5 rounded-full border border-indigo-500/20">
          <Loader2 className="w-3 h-3 animate-spin" /> Planning
        </span>
      );
    case 'running':
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-blue-300 bg-blue-500/15 px-2.5 py-0.5 rounded-full border border-blue-500/30 animate-pulse">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-ping"></span>
          Running
        </span>
      );
    case 'completed':
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-300 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
          <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Completed
        </span>
      );
    case 'needs_review':
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
          <RotateCw className="w-3 h-3 animate-spin" /> Needs Review
        </span>
      );
    case 'failed':
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-rose-300 bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/20">
          <AlertCircle className="w-3 h-3 text-rose-400" /> Failed
        </span>
      );
  }
};

export const AgentCard: React.FC<AgentCardProps> = ({ step, onClick }) => {
  const isRunning = step.status === 'running';
  const isCompleted = step.status === 'completed';

  // Extract preview text
  let previewText = '';
  if (step.output_data) {
    if (typeof step.output_data === 'string') {
      previewText = step.output_data;
    } else if (step.output_data.summary) {
      previewText = step.output_data.summary;
    } else if (step.output_data.executive_summary) {
      previewText = step.output_data.executive_summary;
    } else if (step.output_data.explanation) {
      previewText = step.output_data.explanation;
    } else if (step.output_data.risk_summary) {
      previewText = step.output_data.risk_summary;
    } else if (step.output_data.evaluation_summary) {
      previewText = step.output_data.evaluation_summary;
    }
  }

  return (
    <div
      onClick={onClick}
      className={`glass-card rounded-2xl p-4 cursor-pointer relative overflow-hidden transition-all duration-200 group ${
        isRunning 
          ? 'border-blue-500/60 ring-1 ring-blue-500/40 bg-blue-950/20 shadow-lg shadow-blue-500/10' 
          : 'hover:border-slate-600'
      }`}
    >
      {/* Top status bar shimmer if running */}
      {isRunning && (
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-cyan-400 to-indigo-500 animate-pulse" />
      )}

      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-slate-800/80 border border-slate-700/60 shadow-inner group-hover:scale-105 transition-transform">
            {getAgentIcon(step.agent_id)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono text-slate-500">Step {step.step_order}</span>
              <h4 className="font-semibold text-sm text-slate-100">{step.agent_name}</h4>
            </div>
            <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">
              {step.operation || 'Pending assignment'}
            </p>
          </div>
        </div>
        <div>
          {getStatusBadge(step.status)}
        </div>
      </div>

      {/* Output preview or current action */}
      <div className="mt-3.5 pt-3 border-t border-slate-800/70 text-xs">
        {isRunning && (
          <div className="flex items-center gap-2 text-blue-400 font-mono py-1">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>Processing agent task...</span>
          </div>
        )}

        {isCompleted && previewText && (
          <p className="text-slate-300 text-xs line-clamp-2 leading-relaxed">
            {previewText}
          </p>
        )}

        {step.status === 'waiting' && (
          <p className="text-slate-500 italic">Waiting for upstream dependencies...</p>
        )}

        {step.status === 'failed' && (
          <p className="text-rose-400">{step.error_message || 'Agent error encountered.'}</p>
        )}
      </div>

      {/* Footer metadata */}
      <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-800/40">
        <div className="flex items-center gap-3">
          {step.duration_seconds && step.duration_seconds > 0 ? (
            <span className="font-mono text-slate-400">Duration: {formatDuration(step.duration_seconds)}</span>
          ) : isRunning ? (
            <span className="font-mono text-blue-400 animate-pulse">Running now...</span>
          ) : (
            <span>Queued</span>
          )}
          {step.retry_count && step.retry_count > 0 ? (
            <span className="text-amber-400">Revision #{step.retry_count}</span>
          ) : null}
        </div>
        <span className="text-blue-400 group-hover:translate-x-0.5 transition-transform flex items-center gap-0.5 font-medium">
          View details <ChevronRight className="w-3.5 h-3.5" />
        </span>
      </div>
    </div>
  );
};
