import React, { useState, useEffect, useRef } from 'react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { chatApi, ChatMessageData } from '../../services/chatApi';
import { wsService } from '../../services/websocketService';
import { Plus, Trash2, MessageSquare, Terminal } from 'lucide-react';

interface ChatProps {
  initialPrompt?: string;
  initialAgent?: string;
  onClearInitialPrompt?: () => void;
  onPendingTicketsChange?: (count: number) => void;
}

export const Chat: React.FC<ChatProps> = ({
  initialPrompt,
  initialAgent,
  onClearInitialPrompt,
  onPendingTicketsChange,
}) => {
  const [messages, setMessages] = useState<ChatMessageData[]>([
    {
      id: 'welcome-msg',
      sessionId: 'default',
      sender: 'assistant',
      content: 'Greetings. I am **Nexus Orchestrator**, the central intelligence of your desktop environment.\n\nAll 9 specialized agents are initialized. How may I coordinate your workflow today?',
      timestamp: new Date().toISOString(),
      agentRole: 'orchestrator',
      status: 'completed',
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState('default');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Subscribe to WebSocket live events
  useEffect(() => {
    const unsubTrace = wsService.subscribe('agent_trace', (traceData) => {
      // Append trace to latest message if available
      setMessages((prev) => {
        if (prev.length === 0) return prev;
        const last = { ...prev[prev.length - 1] };
        if (last.sender === 'assistant') {
          const traces = [...(last.activityTraces || []), traceData.data];
          last.activityTraces = traces;
          return [...prev.slice(0, -1), last];
        }
        return prev;
      });
    });

    const unsubSecurity = wsService.subscribe('security_ticket', (ticketPayload) => {
      const ticket = ticketPayload.data;
      if (ticket.status === 'pending') {
        setMessages((prev) => {
          if (prev.length === 0) return prev;
          const last = { ...prev[prev.length - 1] };
          if (last.sender === 'assistant') {
            (last as any).securityTicket = ticket;
            return [...prev.slice(0, -1), last];
          }
          return prev;
        });
        if (onPendingTicketsChange) onPendingTicketsChange(1);
      } else {
        if (onPendingTicketsChange) onPendingTicketsChange(0);
      }
    });

    return () => {
      unsubTrace();
      unsubSecurity();
    };
  }, [onPendingTicketsChange]);

  // Trigger initial prompt if passed from Home quick actions
  useEffect(() => {
    if (initialPrompt) {
      handleSendMessage(initialPrompt, initialAgent);
      if (onClearInitialPrompt) onClearInitialPrompt();
    }
  }, [initialPrompt]);

  const handleSendMessage = async (content: string, targetAgent?: string) => {
    const userMsg: ChatMessageData = {
      id: `usr-${Date.now()}`,
      sessionId: currentSessionId,
      sender: 'user',
      content,
      timestamp: new Date().toISOString(),
      status: 'completed',
    };

    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const response = await chatApi.sendMessage({
        session_id: currentSessionId,
        message: content,
        target_agent: targetAgent,
      });

      setMessages((prev) => [...prev, response]);
      if (response.securityTicketId && onPendingTicketsChange) {
        onPendingTicketsChange(1);
      }
    } catch (err: any) {
      const errorMsg: ChatMessageData = {
        id: `err-${Date.now()}`,
        sessionId: currentSessionId,
        sender: 'assistant',
        content: `⚠️ Communication error with Nexus Backend: ${err.message || 'Check if uvicorn is running on port 8000.'}`,
        timestamp: new Date().toISOString(),
        agentRole: 'orchestrator',
        status: 'failed',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleSecurityResolved = (ticketId: string, decision: 'approved' | 'rejected') => {
    setMessages((prev) =>
      prev.map((msg) => {
        if ((msg as any).securityTicket?.id === ticketId) {
          const updated = { ...msg };
          delete (updated as any).securityTicket;
          updated.content += `\n\n*Security Gate: Action was **${decision.toUpperCase()}** by user.*`;
          return updated;
        }
        return msg;
      })
    );
    if (onPendingTicketsChange) onPendingTicketsChange(0);
  };

  const clearChat = () => {
    setMessages([
      {
        id: `init-${Date.now()}`,
        sessionId: currentSessionId,
        sender: 'assistant',
        content: 'Conversation history reset. System memory cleared for current session.',
        timestamp: new Date().toISOString(),
        agentRole: 'orchestrator',
        status: 'completed',
      },
    ]);
  };

  return (
    <div className="h-full flex flex-col justify-between bg-nexus-bg">
      {/* Chat Header */}
      <div className="h-12 border-b border-nexus-border px-6 flex items-center justify-between bg-nexus-surface/40 backdrop-blur-sm">
        <div className="flex items-center space-x-2">
          <MessageSquare className="w-4 h-4 text-nexus-cyan" />
          <span className="text-xs font-bold tracking-wider text-slate-200 uppercase">
            Interactive Dialogue Stream
          </span>
          <span className="text-[10px] font-mono text-slate-500 px-1.5 py-0.5 rounded bg-nexus-card border border-nexus-border">
            session: {currentSessionId}
          </span>
        </div>

        <button
          onClick={clearChat}
          className="flex items-center space-x-1 text-xs text-slate-400 hover:text-nexus-rose transition-colors p-1"
          title="Clear active dialogue"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Clear</span>
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-2">
        {messages.map((msg) => (
          <ChatMessage
            key={msg.id}
            message={msg}
            onSecurityResolved={handleSecurityResolved}
          />
        ))}

        {loading && (
          <div className="flex items-center space-x-3 my-4">
            <div className="w-8 h-8 rounded-xl bg-nexus-cyan/20 border border-nexus-cyan flex items-center justify-center text-nexus-cyan">
              <Terminal className="w-4 h-4 animate-spin" />
            </div>
            <div className="p-3 rounded-2xl glass-panel text-xs text-slate-300 flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-nexus-cyan animate-ping" />
              <span>Nexus Orchestrator delegating & synthesizing pipeline...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input */}
      <ChatInput onSendMessage={handleSendMessage} disabled={loading} />
    </div>
  );
};
