import React from 'react';
import { AlertTriangle, ShieldCheck, XCircle, CheckCircle2 } from 'lucide-react';
import { request } from '../services/api';

export interface SecurityTicketProps {
  ticket: {
    id: string;
    riskLevel: string;
    operationName: string;
    description: string;
    commandOrPayload: string;
    agentRole: string;
    status: string;
  };
  onResolved: (ticketId: string, decision: 'approved' | 'rejected') => void;
}

export const SecurityModal: React.FC<SecurityTicketProps> = ({ ticket, onResolved }) => {
  const [resolving, setResolving] = React.useState(false);

  const handleDecision = async (decision: 'approved' | 'rejected') => {
    setResolving(true);
    try {
      await request('/api/system/security/resolve', {
        method: 'POST',
        body: JSON.stringify({ ticket_id: ticket.id, decision }),
      });
      onResolved(ticket.id, decision);
    } catch (err) {
      console.error('Failed to resolve security ticket', err);
    } finally {
      setResolving(false);
    }
  };

  return (
    <div className="my-3 p-4 rounded-xl border-2 border-nexus-amber/70 bg-nexus-card/90 shadow-amber-glow animate-pulse">
      <div className="flex items-start space-x-3">
        <div className="p-2 rounded-lg bg-nexus-amber/20 text-nexus-amber shrink-0 mt-0.5">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div className="flex-1 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-nexus-amber">
              Security Gate — Authorization Required
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-nexus-surface border border-nexus-amber/40 text-nexus-amber">
              {ticket.id}
            </span>
          </div>

          <p className="text-sm font-medium text-slate-200">
            Nexus wants permission to execute:
          </p>

          <div className="p-2.5 rounded-lg bg-nexus-bg border border-nexus-border font-mono text-xs text-nexus-cyan overflow-x-auto">
            {ticket.commandOrPayload || ticket.description}
          </div>

          <div className="text-xs text-slate-400">
            Requested by agent: <strong className="text-slate-200 font-mono">{ticket.agentRole}</strong> ({ticket.operationName})
          </div>

          <div className="flex items-center space-x-3 pt-2">
            <button
              onClick={() => handleDecision('rejected')}
              disabled={resolving}
              className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg bg-nexus-surface hover:bg-nexus-rose/20 text-slate-300 hover:text-nexus-rose border border-nexus-border text-xs font-semibold transition-all disabled:opacity-50"
            >
              <XCircle className="w-4 h-4" />
              <span>Cancel</span>
            </button>
            <button
              onClick={() => handleDecision('approved')}
              disabled={resolving}
              className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg bg-nexus-amber hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-amber-glow transition-all disabled:opacity-50"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Allow Execution</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
