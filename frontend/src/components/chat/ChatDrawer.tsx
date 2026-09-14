import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Copy, Check, Sparkles, CornerDownLeft, RotateCcw } from 'lucide-react';
import { ChatMessage } from '../../types';
import { api } from '../../services/api';
import { copyToClipboard } from '../../utils/formatters';

interface ChatDrawerProps {
  taskId: string | null;
  taskTitle?: string;
}

export const ChatDrawer: React.FC<ChatDrawerProps> = ({ taskId, taskTitle }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadHistory();
  }, [taskId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const loadHistory = async () => {
    try {
      const msgs = await api.getChatMessages(taskId || undefined);
      if (msgs.length > 0) {
        setMessages(msgs);
      } else {
        setMessages([
          {
            id: 'welcome',
            role: 'assistant',
            content: `Hello! I have loaded the full analytical context for "${taskTitle || 'your task'}". Feel free to ask me follow-up questions, request deeper dives on specific regions or risks, or ask for tactical execution steps.`
          }
        ]);
      }
    } catch {
      setMessages([
        {
          id: 'welcome',
          role: 'assistant',
          content: 'Context loaded. What would you like to explore regarding this analysis?'
        }
      ]);
    }
  };

  const handleSend = async (customPrompt?: string) => {
    const textToSend = customPrompt || input.trim();
    if (!textToSend || loading) return;

    setInput('');
    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: textToSend
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setLoading(true);

    try {
      const resp = await api.sendChatMessage(textToSend, taskId || undefined);
      setMessages((prev) => [...prev, resp]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: `I encountered an issue processing your request: ${err.message}`
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async (id: string, text: string) => {
    const ok = await copyToClipboard(text);
    if (ok) {
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  const quickQuestions = [
    "What are the most important points?",
    "What are the key deliverables and next steps?",
    "Summarize our technical risk exposure"
  ];

  return (
    <div className="flex flex-col h-full bg-[#0a0d14] border-l border-slate-800/80">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/40">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h4 className="font-semibold text-xs text-slate-100">Task Intelligence Chat</h4>
            <p className="text-[10px] text-slate-400 truncate max-w-[200px]">
              Intent-aware contextual assistant
            </p>
          </div>
        </div>
        <button
          onClick={loadHistory}
          title="Refresh conversation"
          className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Messages List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
        {messages.map((m) => {
          const isUser = m.role === 'user';
          return (
            <div
              key={m.id}
              className={`flex gap-2.5 ${isUser ? 'justify-end' : 'justify-start'}`}
            >
              {!isUser && (
                <div className="w-6 h-6 rounded-lg bg-blue-600/20 border border-blue-500/30 text-blue-400 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Sparkles className="w-3.5 h-3.5" />
                </div>
              )}

              <div
                className={`max-w-[85%] rounded-2xl p-3 shadow-sm relative group ${
                  isUser
                    ? 'bg-blue-600 text-white rounded-br-none'
                    : 'bg-slate-900/90 border border-slate-800 text-slate-200 rounded-bl-none leading-relaxed whitespace-pre-line'
                }`}
              >
                {!isUser && (m.intent || (m.execution_steps && m.execution_steps.length > 0)) && (
                  <div className="space-y-1.5 mb-2">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      {m.intent && (
                        <span
                          className={`text-[9px] font-medium tracking-wide uppercase px-2 py-0.5 rounded-full border ${
                            m.intent === 'GENERAL_QUESTION'
                              ? 'bg-purple-500/15 text-purple-300 border-purple-500/30'
                              : m.intent === 'NEW_TASK'
                              ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                              : m.intent === 'TASK_FOLLOW_UP'
                              ? 'bg-blue-500/15 text-blue-300 border-blue-500/30'
                              : m.intent === 'TASK_RELATED'
                              ? 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30'
                              : 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                          }`}
                        >
                          {m.intent.replace(/_/g, ' ')}
                        </span>
                      )}
                      {m.usedTaskContext && (
                        <span className="text-[9px] text-slate-400">
                          • task context
                        </span>
                      )}
                    </div>
                    {m.execution_steps && m.execution_steps.length > 0 && (
                      <div className="flex flex-wrap gap-1 pt-0.5">
                        {m.execution_steps.map((step, idx) => (
                          <span
                            key={idx}
                            className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-300 border border-slate-700/60 font-mono"
                          >
                            ⚡ {step}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {m.content}

                {!isUser && (
                  <button
                    onClick={() => handleCopy(m.id, m.content)}
                    className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded"
                    title="Copy message"
                  >
                    {copiedId === m.id ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  </button>
                )}
              </div>

              {isUser && (
                <div className="w-6 h-6 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <User className="w-3.5 h-3.5" />
                </div>
              )}
            </div>
          );
        })}

        {loading && (
          <div className="flex gap-2.5 items-center text-slate-400 italic text-xs pl-8">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-ping"></span>
            <span>Nexus AI is thinking...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Questions */}
      <div className="px-4 py-2 border-t border-slate-800/60 bg-slate-950/40 flex flex-wrap gap-1.5">
        {quickQuestions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(q)}
            className="text-[11px] px-2.5 py-1 bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-white rounded-full border border-slate-800 transition-colors"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <div className="p-3 border-t border-slate-800 bg-slate-900/50">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask follow-up questions about this task..."
            className="flex-1 glass-input px-3.5 py-2 rounded-xl text-xs focus:outline-none"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="p-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white rounded-xl shadow-md transition-all"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>
    </div>
  );
};
