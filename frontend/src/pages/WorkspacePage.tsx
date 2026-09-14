import React, { useState, useEffect } from 'react';
import { 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  Loader2, 
  Download, 
  FileText, 
  MessageSquare, 
  Sparkles, 
  ShieldCheck, 
  RefreshCw,
  XCircle,
  Brain,
  Share2,
  ChevronRight,
  Copy,
  Check
} from 'lucide-react';
import { Task, TaskStep, Report } from '../types';
import { AgentCard } from '../components/workspace/AgentCard';
import { WorkflowGraph } from '../components/workspace/WorkflowGraph';
import { StepDetailModal } from '../components/workspace/StepDetailModal';
import { ReportModal } from '../components/reports/ReportModal';
import { ChatDrawer } from '../components/chat/ChatDrawer';
import { formatDuration, formatDate, downloadFile } from '../utils/formatters';
import { api } from '../services/api';

interface WorkspacePageProps {
  task: Task | null;
  onRefreshTask: () => void;
  onCancelTask: () => void;
  isStreaming: boolean;
}

export const WorkspacePage: React.FC<WorkspacePageProps> = ({
  task,
  onRefreshTask,
  onCancelTask,
  isStreaming
}) => {
  const [selectedStep, setSelectedStep] = useState<TaskStep | null>(null);
  const [viewMode, setViewMode] = useState<'cards' | 'graph'>('cards');
  const [activeReport, setActiveReport] = useState<Report | null>(null);
  const [loadingReport, setLoadingReport] = useState(false);
  const [showChat, setShowChat] = useState(true);
  const [activeTab, setActiveTab] = useState<'solution' | 'workflow'>('solution');
  const [copied, setCopied] = useState(false);
  const [retrying, setRetrying] = useState(false);

  const handleRetryTask = async () => {
    if (!task?.id || retrying) return;
    setRetrying(true);
    try {
      await api.runTask(task.id);
      onRefreshTask();
    } catch {
      // ignore
    } finally {
      setRetrying(false);
    }
  };

  useEffect(() => {
    if (task?.status === 'completed' && task.final_result) {
      setActiveTab('solution');
    } else if (task?.status === 'running') {
      setActiveTab('workflow');
    }
  }, [task?.status, task?.id]);

  const handleCopyResult = () => {
    if (task?.final_result) {
      navigator.clipboard.writeText(task.final_result);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!task) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-400">
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 mb-4">
          <Brain className="w-8 h-8 text-blue-400 animate-pulse" />
        </div>
        <h3 className="text-lg font-semibold text-slate-200">No Active Workspace</h3>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Select an existing task from History or create a new intelligent workflow from the Dashboard.
        </p>
      </div>
    );
  }

  const isCompleted = task.status === 'completed';
  const isRunning = task.status === 'running';

  const handleOpenReport = async () => {
    setLoadingReport(true);
    try {
      // Find report corresponding to this task
      const reports = await api.listReports();
      const match = reports.find(r => r.task_id === task.id);
      if (match) {
        setActiveReport(match);
      } else if (reports.length > 0) {
        // Fallback to latest
        setActiveReport(reports[0]);
      }
    } catch (err) {
      console.error("Failed to load report", err);
    } finally {
      setLoadingReport(false);
    }
  };

  const handleDownloadReportMD = async () => {
    try {
      const reports = await api.listReports();
      const match = reports.find(r => r.task_id === task.id) || reports[0];
      if (match && match.full_markdown) {
        const filename = `${match.title.toLowerCase().replace(/[^a-z0-9]/g, '_')}.md`;
        downloadFile(match.full_markdown, filename, 'text/markdown');
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex-1 flex overflow-hidden bg-[#07090e]">
      {/* Main Workspace Canvas */}
      <div className="flex-1 flex flex-col overflow-hidden border-r border-slate-800/80">
        {/* Workspace Top Toolbar */}
        <div className="px-6 py-3.5 border-b border-slate-800/80 bg-[#090d15] flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-sm text-slate-100">{task.title}</h3>
                {task.is_demo && (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 uppercase font-semibold">
                    Demo
                  </span>
                )}
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                  isCompleted ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                  isRunning ? 'bg-blue-500/15 text-blue-400 border-blue-500/30' :
                  'bg-slate-800 text-slate-400 border-slate-700'
                }`}>
                  {isCompleted ? 'COMPLETED' : (isRunning ? 'RUNNING' : task.status.toUpperCase())}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 line-clamp-1 max-w-lg">
                {task.user_prompt}
              </p>
            </div>
          </div>

          {/* Primary Solution vs Agent Workflow Tabs */}
          <div className="flex items-center gap-2">
            <div className="flex rounded-xl bg-slate-900 border border-slate-800 p-1 text-xs">
              <button
                type="button"
                onClick={() => setActiveTab('solution')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all font-medium ${
                  activeTab === 'solution'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Solution</span>
                {isCompleted && <Check className="w-3 h-3 text-emerald-300" />}
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('workflow')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all font-medium ${
                  activeTab === 'workflow'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <span>Agent Steps ({task.steps.length})</span>
              </button>
            </div>

            {/* Workflow sub-toggle if viewing workflow */}
            {activeTab === 'workflow' && (
              <div className="hidden sm:flex rounded-lg bg-slate-900/80 border border-slate-800 p-0.5 text-xs">
                <button
                  type="button"
                  onClick={() => setViewMode('cards')}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all ${
                    viewMode === 'cards' ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Cards
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode('graph')}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all ${
                    viewMode === 'graph' ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Pipeline
                </button>
              </div>
            )}

            <button
              type="button"
              onClick={() => setShowChat(!showChat)}
              className={`p-2 rounded-xl border text-xs font-medium transition-colors ${
                showChat ? 'bg-blue-600/20 border-blue-500/30 text-blue-300' : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200'
              }`}
              title="Toggle Follow-up Chat"
            >
              <MessageSquare className="w-4 h-4" />
            </button>

            {isRunning && (
              <button
                type="button"
                onClick={onCancelTask}
                className="flex items-center gap-1 px-3 py-1.5 bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 rounded-xl text-xs font-medium transition-colors"
              >
                <XCircle className="w-3.5 h-3.5" />
                Cancel
              </button>
            )}

            <button
              type="button"
              onClick={onRefreshTask}
              className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl border border-slate-700 transition-colors"
              title="Refresh Task"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Workspace Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Running progress status bar */}
          {isRunning && (
            <div className="glass-panel p-4 rounded-2xl border border-blue-500/40 bg-blue-950/20 flex items-center justify-between animate-pulse">
              <div className="flex items-center gap-3">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
                </span>
                <div>
                  <div className="text-xs font-semibold text-blue-200 uppercase tracking-wide">
                    Task in Progress...
                  </div>
                  <div className="text-xs text-slate-400">
                    Specialized AI agents are analyzing and synthesizing the final answer.
                  </div>
                </div>
              </div>
              <div className="text-xs font-mono text-blue-400">
                {isStreaming ? 'Streaming...' : 'Executing...'}
              </div>
            </div>
          )}

          {/* TAB 1: SOLUTION / ANSWER */}
          {activeTab === 'solution' && (
            <div className="space-y-6">
              {isCompleted && task.final_result ? (
                <div className="glass-panel rounded-2xl p-6 border border-emerald-500/30 bg-slate-900/50 shadow-xl space-y-5 animate-in fade-in">
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                        <CheckCircle2 className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-white">
                          Final Answer & Insights
                        </h3>
                        <p className="text-xs text-slate-400">
                          Verified by Reviewer Agent • Completed in {formatDuration(task.duration_seconds)}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={handleCopyResult}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium border border-slate-700 transition-colors"
                      >
                        {copied ? (
                          <>
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                            <span className="text-emerald-400">Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5 text-slate-400" />
                            <span>Copy Answer</span>
                          </>
                        )}
                      </button>

                      <button
                        type="button"
                        onClick={handleOpenReport}
                        disabled={loadingReport}
                        className="flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium shadow transition-colors"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>View Full Report</span>
                      </button>

                      <button
                        type="button"
                        onClick={handleDownloadReportMD}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium border border-slate-700 transition-colors"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download MD</span>
                      </button>
                    </div>
                  </div>

                  {/* Contributing Agents Badges */}
                  <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
                    <span className="text-slate-400 text-[11px] font-medium">Contributed by:</span>
                    {task.steps.map((s) => (
                      <button
                        key={s.id}
                        type="button"
                        onClick={() => setSelectedStep(s)}
                        className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700/60 text-[11px] font-medium transition-colors"
                      >
                        {s.agent_name}
                      </button>
                    ))}
                  </div>

                  {/* Formatted Answer Body */}
                  <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-line font-sans pt-2 border-t border-slate-800/60">
                    {task.final_result}
                  </div>
                </div>
              ) : (isRunning || task.status === 'pending') ? (
                <div className="glass-panel rounded-2xl p-10 text-center space-y-4 border border-blue-500/30 bg-blue-950/10 animate-in fade-in">
                  <div className="w-12 h-12 rounded-2xl bg-blue-500/15 text-blue-400 flex items-center justify-center mx-auto border border-blue-500/30 shadow-lg shadow-blue-500/10">
                    <Loader2 className="w-6 h-6 animate-spin" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white tracking-tight">
                      {task.status === 'pending' ? 'Initializing Workflow & Scheduling Agents...' : 'Agents Are Executing Your Task...'}
                    </h3>
                    <p className="text-xs text-slate-400 max-w-md mx-auto mt-1 leading-relaxed">
                      Nexus Orchestrator is analyzing your request, delegating subtasks to specialized agents, and preparing the final solution.
                    </p>
                  </div>
                  <div className="flex items-center justify-center gap-2 pt-2">
                    <button
                      type="button"
                      onClick={() => setActiveTab('workflow')}
                      className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold shadow transition-colors"
                    >
                      View Live Agent Steps ({task.steps.length})
                    </button>
                    <button
                      type="button"
                      onClick={onRefreshTask}
                      className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-medium border border-slate-700 transition-colors"
                    >
                      <RefreshCw className="w-3 h-3" />
                      <span>Refresh</span>
                    </button>
                  </div>
                </div>
              ) : task.status === 'failed' ? (
                <div className="glass-panel rounded-2xl p-8 text-center text-xs space-y-4 border border-rose-500/30 bg-rose-950/10 animate-in fade-in">
                  <div className="w-10 h-10 rounded-2xl bg-rose-500/15 text-rose-400 flex items-center justify-center mx-auto border border-rose-500/30">
                    <AlertCircle className="w-5 h-5" />
                  </div>
                  <div className="space-y-1">
                    <h4 className="text-sm font-semibold text-rose-200">Task Execution Encountered an Issue</h4>
                    <p className="text-slate-400 max-w-md mx-auto leading-relaxed">
                      {task.error_message || 'An error occurred during workflow execution. You can retry the task or inspect individual step cards.'}
                    </p>
                  </div>
                  <div className="flex items-center justify-center gap-2 pt-1">
                    <button
                      type="button"
                      onClick={handleRetryTask}
                      disabled={retrying}
                      className="inline-flex items-center gap-1.5 px-4 py-2 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold shadow transition-colors"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 ${retrying ? 'animate-spin' : ''}`} />
                      <span>{retrying ? 'Retrying...' : 'Retry Task'}</span>
                    </button>
                    <button
                      type="button"
                      onClick={onRefreshTask}
                      className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-medium border border-slate-700 transition-colors"
                    >
                      <span>Refresh</span>
                    </button>
                  </div>
                </div>
              ) : (
                <div className="glass-panel rounded-2xl p-8 text-center text-xs text-slate-400 space-y-3">
                  <p>No final solution available yet for this task.</p>
                  <button
                    type="button"
                    onClick={onRefreshTask}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-medium border border-slate-700 transition-colors"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Refresh Task</span>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: AGENT WORKFLOW & STEPS */}
          {activeTab === 'workflow' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="font-semibold uppercase tracking-wider">
                  AI Agents Involved ({task.steps.length} Steps)
                </span>
                <span className="text-[11px] text-slate-500">Click any card to inspect what the agent found</span>
              </div>

              {viewMode === 'graph' ? (
                <div className="glass-panel rounded-2xl p-4">
                  <WorkflowGraph
                    userPrompt={task.user_prompt}
                    steps={task.steps}
                    onSelectStep={setSelectedStep}
                    selectedStepId={selectedStep?.id}
                  />
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                  {task.steps.map((step) => (
                    <AgentCard
                      key={step.id}
                      step={step}
                      onClick={() => setSelectedStep(step)}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Side Chat Drawer */}
      {showChat && (
        <div className="w-80 sm:w-96 flex-shrink-0">
          <ChatDrawer taskId={task.id} taskTitle={task.title} />
        </div>
      )}

      {/* Step Detail Modal */}
      <StepDetailModal
        step={selectedStep}
        onClose={() => setSelectedStep(null)}
      />

      {/* Full Report Modal */}
      <ReportModal
        report={activeReport}
        onClose={() => setActiveReport(null)}
      />
    </div>
  );
};
