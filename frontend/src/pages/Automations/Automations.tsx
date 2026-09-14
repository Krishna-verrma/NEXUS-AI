import React, { useState, useEffect } from 'react';
import { Zap, Play, Clock, CheckCircle2, Power, RefreshCw } from 'lucide-react';
import { automationApi, AutomationData } from '../../services/automationApi';

export const Automations: React.FC = () => {
  const [automations, setAutomations] = useState<AutomationData[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggeringId, setTriggeringId] = useState<string | null>(null);

  const loadAutomations = async () => {
    try {
      setLoading(true);
      const data = await automationApi.getAutomations();
      setAutomations(data);
    } catch (err) {
      console.error('Failed to load automations', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAutomations();
  }, []);

  const handleToggle = async (id: string) => {
    try {
      const res = await automationApi.toggleAutomation(id);
      if (res.success) {
        setAutomations((prev) =>
          prev.map((a) => (a.id === id ? { ...a, enabled: res.automation.enabled } : a))
        );
      }
    } catch (err) {
      console.error('Error toggling automation', err);
    }
  };

  const handleTrigger = async (id: string) => {
    setTriggeringId(id);
    try {
      await automationApi.triggerAutomation(id);
      loadAutomations();
    } catch (err) {
      console.error('Error triggering automation', err);
    } finally {
      setTriggeringId(null);
    }
  };

  return (
    <div className="h-full overflow-y-auto px-8 py-8 space-y-8 bg-nexus-bg">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-nexus-border pb-6">
        <div>
          <div className="flex items-center space-x-2">
            <Zap className="w-5 h-5 text-nexus-cyan" />
            <h1 className="text-2xl font-extrabold text-white tracking-tight">
              Autonomous Workflows
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Cron-scheduled and event-reactive automation pipelines executed by specialized agents.
          </p>
        </div>

        <button
          onClick={loadAutomations}
          className="p-2 rounded-xl bg-nexus-surface hover:bg-nexus-card text-slate-400 hover:text-white border border-nexus-border transition-colors self-start sm:self-auto"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Rules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {automations.map((rule) => (
          <div
            key={rule.id}
            className={`glass-panel p-5 rounded-2xl border transition-all ${
              rule.enabled ? 'border-nexus-border' : 'border-nexus-border/40 opacity-70'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-2">
                <div className={`p-2 rounded-xl border ${rule.enabled ? 'bg-nexus-cyan/15 border-nexus-cyan/30 text-nexus-cyan' : 'bg-slate-800 border-slate-700 text-slate-500'}`}>
                  <Zap className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">{rule.name}</h3>
                  <span className="text-[10px] font-mono text-slate-500 uppercase">
                    {rule.trigger_type} • {rule.trigger_schedule}
                  </span>
                </div>
              </div>

              {/* Toggle Switch */}
              <button
                onClick={() => handleToggle(rule.id)}
                className={`p-1.5 rounded-lg border transition-colors ${
                  rule.enabled
                    ? 'bg-nexus-emerald/20 border-nexus-emerald text-nexus-emerald'
                    : 'bg-nexus-surface border-nexus-border text-slate-500'
                }`}
                title={rule.enabled ? 'Enabled (Click to disable)' : 'Disabled (Click to enable)'}
              >
                <Power className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-400 mt-4 leading-relaxed font-normal">
              {rule.description}
            </p>

            {/* Prompt snippet */}
            <div className="mt-3 p-2.5 rounded-lg bg-nexus-card border border-nexus-border text-[11px] font-mono text-slate-300">
              <span className="text-slate-500">Target Agent:</span>{' '}
              <strong className="text-nexus-cyan">{rule.target_agent}</strong>
              <div className="text-slate-400 mt-1 truncate">"{rule.action_prompt}"</div>
            </div>

            {/* Footer */}
            <div className="mt-5 pt-4 border-t border-nexus-border/60 flex items-center justify-between text-xs">
              <div className="text-[10px] font-mono text-slate-500">
                {rule.last_run ? `Last run: ${new Date(rule.last_run).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'Not run yet'}
              </div>

              <button
                onClick={() => handleTrigger(rule.id)}
                disabled={triggeringId === rule.id}
                className="flex items-center space-x-1 px-3 py-1 rounded-lg bg-nexus-surface hover:bg-nexus-cyan/10 hover:text-nexus-cyan border border-nexus-border text-xs font-semibold transition-all disabled:opacity-50"
              >
                <Play className="w-3 h-3" />
                <span>{triggeringId === rule.id ? 'Running...' : 'Trigger Now'}</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
