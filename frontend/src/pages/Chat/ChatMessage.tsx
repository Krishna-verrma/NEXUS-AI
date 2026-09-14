import React, { useState } from 'react';
import { Bot, User, Copy, Check, Terminal } from 'lucide-react';
import { AgentActivity } from './AgentActivity';
import { SecurityModal } from '../../components/SecurityModal';

interface ChatMessageProps {
  message: {
    id: string;
    sender: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    agentRole?: string;
    activityTraces?: any[];
    securityTicket?: any;
  };
  onSecurityResolved?: (ticketId: string, decision: 'approved' | 'rejected') => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, onSecurityResolved }) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.sender === 'user';

  const copyContent = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Format markdown snippets safely
  const renderFormattedContent = (content: string) => {
    // Check if contains code blocks
    if (content.includes('```')) {
      const parts = content.split(/(```[\s\S]*?```)/g);
      return parts.map((part, idx) => {
        if (part.startsWith('```')) {
          const lines = part.slice(3, -3).trim().split('\n');
          const lang = lines[0].trim();
          const code = (lang ? lines.slice(1) : lines).join('\n');
          return (
            <div key={idx} className="my-2 rounded-lg bg-nexus-bg border border-nexus-border overflow-hidden">
              <div className="flex items-center justify-between px-3 py-1.5 bg-nexus-surface/80 border-b border-nexus-border text-[11px] font-mono text-slate-400">
                <div className="flex items-center space-x-1.5">
                  <Terminal className="w-3.5 h-3.5 text-nexus-cyan" />
                  <span>{lang || 'code'}</span>
                </div>
                <button
                  onClick={() => navigator.clipboard.writeText(code)}
                  className="hover:text-white transition-colors"
                >
                  Copy
                </button>
              </div>
              <pre className="p-3 text-xs font-mono text-slate-200 overflow-x-auto">
                <code>{code}</code>
              </pre>
            </div>
          );
        }
        return <div key={idx} className="whitespace-pre-wrap leading-relaxed">{part}</div>;
      });
    }

    return <div className="whitespace-pre-wrap leading-relaxed">{content}</div>;
  };

  return (
    <div className={`flex items-start space-x-3 my-4 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 border ${
          isUser
            ? 'bg-nexus-violet/20 border-nexus-violet text-nexus-violet'
            : 'bg-nexus-cyan/20 border-nexus-cyan text-nexus-cyan shadow-cyan-glow'
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Bubble Container */}
      <div className={`max-w-2xl space-y-1 ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Header meta */}
        <div className={`flex items-center space-x-2 text-[11px] text-slate-400 ${isUser ? 'justify-end' : ''}`}>
          <span className="font-semibold text-slate-300">
            {isUser ? 'You' : (message.agentRole ? `Nexus (${message.agentRole})` : 'Nexus Orchestrator')}
          </span>
          <span>•</span>
          <span className="font-mono text-[10px]">{message.timestamp ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}</span>
        </div>

        {/* Bubble */}
        <div
          className={`p-4 rounded-2xl text-sm relative group border ${
            isUser
              ? 'bg-nexus-indigo/20 text-white border-nexus-indigo/40 rounded-tr-sm'
              : 'glass-panel text-slate-100 border-nexus-border rounded-tl-sm'
          }`}
        >
          {renderFormattedContent(message.content)}

          {/* Copy Button */}
          <button
            onClick={copyContent}
            className="absolute top-2 right-2 p-1 rounded bg-nexus-surface/60 opacity-0 group-hover:opacity-100 hover:bg-nexus-surface transition-all text-slate-400 hover:text-white"
            title="Copy message"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-nexus-emerald" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>

        {/* Agent Activity Traces */}
        {message.activityTraces && message.activityTraces.length > 0 && (
          <AgentActivity traces={message.activityTraces} />
        )}

        {/* Security Ticket Modal if pending approval */}
        {message.securityTicket && onSecurityResolved && (
          <SecurityModal
            ticket={message.securityTicket}
            onResolved={onSecurityResolved}
          />
        )}
      </div>
    </div>
  );
};
