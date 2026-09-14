import React, { useState, useEffect } from 'react';
import { AgentCard } from './AgentCard';
import { AgentDetails } from './AgentDetails';
import { agentApi, AgentDescriptorData } from '../../services/agentApi';
import { Bot, Search, Sparkles } from 'lucide-react';

interface AgentsProps {
  onRunAgent: (agentRole: string) => void;
}

export const Agents: React.FC<AgentsProps> = ({ onRunAgent }) => {
  const [agents, setAgents] = useState<AgentDescriptorData[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<AgentDescriptorData | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const data = await agentApi.getAgents();
        setAgents(data);
      } catch (err) {
        console.error('Failed to load agents', err);
      } finally {
        setLoading(false);
      }
    };
    fetchAgents();
  }, []);

  const filteredAgents = agents.filter((a) =>
    a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.capabilities.some((c) => c.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="h-full overflow-y-auto px-8 py-8 space-y-8 bg-nexus-bg">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-nexus-border pb-6">
        <div>
          <div className="flex items-center space-x-2">
            <Bot className="w-5 h-5 text-nexus-cyan" />
            <h1 className="text-2xl font-extrabold text-white tracking-tight">
              Nexus Agent Hive
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            9 isolated autonomous sub-agents coordinated by Nexus Orchestrator.
          </p>
        </div>

        {/* Search filter */}
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter agents or capabilities..."
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-nexus-surface/80 border border-nexus-border text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-nexus-cyan transition-colors"
          />
        </div>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAgents.map((agent) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            onSelect={(a) => setSelectedAgent(a)}
            onRunDirect={onRunAgent}
          />
        ))}
      </div>

      {/* Details Modal */}
      <AgentDetails
        agent={selectedAgent}
        onClose={() => setSelectedAgent(null)}
        onRun={onRunAgent}
      />
    </div>
  );
};
