import React, { useState, useEffect } from 'react';
import { ListTodo, Plus, CheckCircle2, Clock, PlayCircle, XCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { taskApi, TaskData } from '../../services/taskApi';

export const Tasks: React.FC = () => {
  const [tasks, setTasks] = useState<TaskData[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newPriority, setNewPriority] = useState('medium');
  const [newAgent, setNewAgent] = useState('orchestrator');

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const data = await taskApi.getTasks();
      setTasks(data);
    } catch (err) {
      console.error('Failed to load tasks', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    try {
      const created = await taskApi.createTask(newTitle.trim(), undefined, newPriority, newAgent);
      setTasks((prev) => [created, ...prev]);
      setNewTitle('');
      setIsCreating(false);
    } catch (err) {
      console.error('Error creating task', err);
    }
  };

  const handleCancelTask = async (taskId: string) => {
    try {
      await taskApi.cancelTask(taskId);
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? { ...t, status: 'cancelled' } : t))
      );
    } catch (err) {
      console.error('Error cancelling task', err);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-nexus-emerald/15 border border-nexus-emerald/40 text-nexus-emerald text-xs font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>COMPLETED</span>
          </span>
        );
      case 'in_progress':
        return (
          <span className="flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-nexus-cyan/15 border border-nexus-cyan/40 text-nexus-cyan text-xs font-semibold">
            <PlayCircle className="w-3.5 h-3.5 animate-spin" />
            <span>RUNNING</span>
          </span>
        );
      case 'cancelled':
        return (
          <span className="flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-nexus-rose/15 border border-nexus-rose/40 text-nexus-rose text-xs font-semibold">
            <XCircle className="w-3.5 h-3.5" />
            <span>CANCELLED</span>
          </span>
        );
      default:
        return (
          <span className="flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-slate-500/15 border border-slate-500/40 text-slate-400 text-xs font-semibold">
            <Clock className="w-3.5 h-3.5" />
            <span>QUEUED</span>
          </span>
        );
    }
  };

  return (
    <div className="h-full overflow-y-auto px-8 py-8 space-y-8 bg-nexus-bg">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-nexus-border pb-6">
        <div>
          <div className="flex items-center space-x-2">
            <ListTodo className="w-5 h-5 text-nexus-cyan" />
            <h1 className="text-2xl font-extrabold text-white tracking-tight">
              Task Execution Matrix
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Asynchronous agent jobs, multi-step subtasks, and progress telemetry.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchTasks}
            className="p-2 rounded-xl bg-nexus-surface hover:bg-nexus-card text-slate-400 hover:text-white border border-nexus-border transition-colors"
            title="Refresh tasks"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={() => setIsCreating(true)}
            className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-nexus-cyan to-nexus-indigo hover:from-cyan-400 hover:to-indigo-500 text-slate-950 font-bold text-xs shadow-cyan-glow transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Create Task</span>
          </button>
        </div>
      </div>

      {/* Create Modal */}
      {isCreating && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleCreateTask} className="glass-panel w-full max-w-md rounded-2xl border border-nexus-cyan/40 p-6 space-y-4 shadow-cyan-glow">
            <h3 className="text-base font-bold text-white tracking-wide">
              Initialize New Agent Task
            </h3>
            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">Task Title</label>
              <input
                type="text"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="e.g. Scrape technical whitepapers and summarize"
                className="w-full px-3 py-2 rounded-xl bg-nexus-surface border border-nexus-border text-xs text-white focus:outline-none focus:border-nexus-cyan"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Priority</label>
                <select
                  value={newPriority}
                  onChange={(e) => setNewPriority(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-nexus-surface border border-nexus-border text-xs text-white focus:outline-none focus:border-nexus-cyan"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Assigned Agent</label>
                <select
                  value={newAgent}
                  onChange={(e) => setNewAgent(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-nexus-surface border border-nexus-border text-xs text-white focus:outline-none focus:border-nexus-cyan"
                >
                  <option value="orchestrator">Orchestrator</option>
                  <option value="file_agent">File Agent</option>
                  <option value="coding_agent">Coding Agent</option>
                  <option value="computer_agent">Computer Agent</option>
                  <option value="web_agent">Web Agent</option>
                </select>
              </div>
            </div>
            <div className="flex items-center justify-end space-x-3 pt-3">
              <button
                type="button"
                onClick={() => setIsCreating(false)}
                className="px-4 py-2 rounded-xl bg-nexus-surface text-slate-300 border border-nexus-border text-xs"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-5 py-2 rounded-xl bg-nexus-cyan text-slate-950 font-bold text-xs shadow-cyan-glow"
              >
                Queue Task
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Task List */}
      <div className="space-y-4">
        {tasks.map((task) => (
          <div key={task.id} className="glass-panel p-5 rounded-2xl border border-nexus-border space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <h3 className="text-sm font-bold text-white">{task.title}</h3>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-nexus-card border border-nexus-border text-slate-400">
                    {task.assignedAgent}
                  </span>
                </div>
                {task.description && (
                  <p className="text-xs text-slate-400">{task.description}</p>
                )}
              </div>
              <div className="flex items-center space-x-3 shrink-0">
                {getStatusBadge(task.status)}
                {task.status === 'in_progress' && (
                  <button
                    onClick={() => handleCancelTask(task.id)}
                    className="text-xs text-nexus-rose hover:underline font-mono"
                  >
                    Cancel
                  </button>
                )}
              </div>
            </div>

            {/* Progress Bar */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span>Execution Progress</span>
                <span>{task.progress}%</span>
              </div>
              <div className="w-full h-1.5 rounded-full bg-nexus-surface overflow-hidden border border-nexus-border/50">
                <div
                  className="h-full bg-gradient-to-r from-nexus-cyan to-nexus-violet transition-all duration-500"
                  style={{ width: `${task.progress}%` }}
                />
              </div>
            </div>

            {/* Sub-steps */}
            {task.steps && task.steps.length > 0 && (
              <div className="pt-2 border-t border-nexus-border/40 space-y-1.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Sub-step Hierarchy
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {task.steps.map((step) => (
                    <div
                      key={step.id}
                      className="p-2 rounded-lg bg-nexus-card/70 border border-nexus-border text-xs flex items-center justify-between"
                    >
                      <div className="flex items-center space-x-2">
                        <div
                          className={`w-2 h-2 rounded-full ${
                            step.status === 'completed'
                              ? 'bg-nexus-emerald'
                              : step.status === 'running'
                              ? 'bg-nexus-cyan animate-ping'
                              : 'bg-slate-500'
                          }`}
                        />
                        <span className="text-slate-300">{step.title}</span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-500 uppercase">
                        {step.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
