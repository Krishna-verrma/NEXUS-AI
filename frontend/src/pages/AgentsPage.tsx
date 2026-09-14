import React, { useState } from 'react';
import { 
  Bot, 
  Brain, 
  Search, 
  Code2, 
  BarChart3, 
  FileText, 
  AlertTriangle, 
  CheckCircle2, 
  FileSpreadsheet, 
  Plus, 
  Sparkles,
  ToggleLeft,
  ToggleRight,
  Calendar
} from 'lucide-react';
import { Agent } from '../types';
import { Modal } from '../components/ui/Modal';

interface AgentsPageProps {
  agents: Agent[];
  onToggleAgent: (agentId: string, isEnabled: boolean) => void;
}

const getAgentIcon = (id: string) => {
  switch (id) {
    case 'orchestrator': return <Brain className="w-6 h-6 text-indigo-400" />;
    case 'data_analyst': return <BarChart3 className="w-6 h-6 text-blue-400" />;
    case 'research': return <Search className="w-6 h-6 text-cyan-400" />;
    case 'coding': return <Code2 className="w-6 h-6 text-emerald-400" />;
    case 'document': return <FileText className="w-6 h-6 text-purple-400" />;
    case 'risk': return <AlertTriangle className="w-6 h-6 text-amber-400" />;
    case 'reviewer': return <CheckCircle2 className="w-6 h-6 text-teal-400" />;
    case 'report': return <FileSpreadsheet className="w-6 h-6 text-rose-400" />;
    case 'schedule': return <Calendar className="w-6 h-6 text-amber-400" />;
    default: return <Bot className="w-6 h-6 text-blue-400" />;
  }
};

export const AgentsPage: React.FC<AgentsPageProps> = ({ agents, onToggleAgent }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [customName, setCustomName] = useState('');
  const [customRole, setCustomRole] = useState('');
  const [customDescription, setCustomDescription] = useState('');

  return (
    <div className="flex-1 overflow-y-auto p-8 max-w-6xl mx-auto space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold text-white tracking-tight">Specialized Agent Registry</h2>
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">
              {agents.length} Active Nodes
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Configure agent capabilities, roles, and collaborative workflows.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-medium rounded-xl shadow-lg shadow-blue-600/20 transition-all border border-blue-400/30"
        >
          <Plus className="w-4 h-4" />
          <span>Create Custom Agent</span>
        </button>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4">
        {agents.map((agent) => (
          <div
            key={agent.id}
            className={`glass-card p-5 rounded-2xl border transition-all ${
              agent.is_enabled ? 'border-slate-800' : 'opacity-60 border-slate-900 bg-slate-950/40'
            }`}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700/60 shadow-inner">
                  {getAgentIcon(agent.id)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold text-slate-100">{agent.name}</h3>
                    {agent.is_system && (
                      <span className="text-[10px] font-mono px-1.5 py-0.2 bg-slate-800 text-slate-400 rounded border border-slate-700">
                        SYSTEM
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-blue-400/90 font-mono mt-0.5">{agent.role}</p>
                </div>
              </div>

              {/* Toggle switch */}
              <button
                onClick={() => onToggleAgent(agent.id, !agent.is_enabled)}
                disabled={agent.id === 'orchestrator' || agent.id === 'reviewer'}
                title={agent.id === 'orchestrator' || agent.id === 'reviewer' ? 'Core system agent cannot be disabled' : 'Toggle Agent'}
                className="text-slate-400 hover:text-slate-200 disabled:opacity-40 transition-colors"
              >
                {agent.is_enabled ? (
                  <ToggleRight className="w-6 h-6 text-blue-400" />
                ) : (
                  <ToggleLeft className="w-6 h-6 text-slate-600" />
                )}
              </button>
            </div>

            <p className="text-xs text-slate-300 mt-3.5 leading-relaxed">
              {agent.description}
            </p>

            {/* Capabilities Chips */}
            <div className="mt-4 pt-3 border-t border-slate-800/70 space-y-1.5">
              <span className="text-[10px] font-mono uppercase text-slate-500 font-semibold tracking-wider">
                Capabilities
              </span>
              <div className="flex flex-wrap gap-1.5">
                {agent.capabilities.map((cap, i) => (
                  <span
                    key={i}
                    className="text-[10px] px-2 py-0.5 rounded-md bg-slate-800/90 text-slate-300 border border-slate-700/60"
                  >
                    {cap}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Create Custom Agent Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create Custom Agent"
        subtitle="Define specialized instructions, domain capabilities, and API integrations"
        maxWidth="lg"
      >
        <div className="space-y-4">
          <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs flex items-center gap-2">
            <Sparkles className="w-4 h-4 flex-shrink-0" />
            <span>
              <strong>Nexus Agent Fabric:</strong> Custom agents will dynamically link into the Orchestrator's execution planner.
            </span>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-mono text-slate-400 uppercase">Agent Name</label>
            <input
              type="text"
              value={customName}
              onChange={(e) => setCustomName(e.target.value)}
              placeholder="e.g. Legal Compliance Auditor"
              className="w-full glass-input px-3.5 py-2 rounded-xl text-xs"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-mono text-slate-400 uppercase">Specialized Role</label>
            <input
              type="text"
              value={customRole}
              onChange={(e) => setCustomRole(e.target.value)}
              placeholder="e.g. Compliance Agent"
              className="w-full glass-input px-3.5 py-2 rounded-xl text-xs"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-mono text-slate-400 uppercase">Mission & Capabilities</label>
            <textarea
              value={customDescription}
              onChange={(e) => setCustomDescription(e.target.value)}
              placeholder="Describe what this agent analyzes, tools it can call, and output schema..."
              rows={3}
              className="w-full glass-input px-3.5 py-2 rounded-xl text-xs resize-none"
            />
          </div>

          <div className="flex items-center justify-between pt-3 border-t border-slate-800">
            <span className="text-[11px] text-amber-400/90 font-mono">
              Custom Agent SDK: Coming in v1.1
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 bg-slate-800 text-slate-300 rounded-xl text-xs hover:bg-slate-700"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => {
                  alert("Custom agent template drafted. This capability will be activated in the next update!");
                  setIsModalOpen(false);
                }}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-medium"
              >
                Save Template
              </button>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
};
