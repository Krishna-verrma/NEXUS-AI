import React, { useState } from 'react';
import { Send, Mic, MicOff, ChevronDown, Sparkles } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string, targetAgent?: string) => void;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled }) => {
  const [input, setInput] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('orchestrator');
  const [isListening, setIsListening] = useState(false);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || disabled) return;
    onSendMessage(input.trim(), selectedAgent === 'orchestrator' ? undefined : selectedAgent);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const toggleVoice = () => {
    if (isListening) {
      setIsListening(false);
      return;
    }

    // Check if web speech recognition is available
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.onstart = () => setIsListening(true);
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInput((prev) => (prev ? `${prev} ${transcript}` : transcript));
        setIsListening(false);
      };
      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);
      recognition.start();
    } else {
      // Simulated voice transcription in demo mode
      setIsListening(true);
      setTimeout(() => {
        setInput('Analyze the latest project architecture and check system vitals');
        setIsListening(false);
      }, 1500);
    }
  };

  const agentOptions = [
    { id: 'orchestrator', name: 'Nexus Orchestrator (Auto)' },
    { id: 'computer_agent', name: 'Computer Controller' },
    { id: 'file_agent', name: 'Filesystem Operator' },
    { id: 'web_agent', name: 'Web Navigator' },
    { id: 'coding_agent', name: 'Code Architect' },
    { id: 'productivity_agent', name: 'Productivity Executive' },
    { id: 'communication_agent', name: 'Comms Dispatcher' },
    { id: 'data_agent', name: 'Data Scientist' },
    { id: 'creative_agent', name: 'Creative Studio' },
  ];

  return (
    <form onSubmit={handleSubmit} className="border-t border-nexus-border bg-nexus-surface/80 backdrop-blur-md p-4 space-y-2">
      <div className="flex items-center justify-between text-xs text-slate-400 px-1">
        {/* Agent Target Picker */}
        <div className="flex items-center space-x-2">
          <Sparkles className="w-3.5 h-3.5 text-nexus-cyan" />
          <span>Routing:</span>
          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            className="bg-nexus-card border border-nexus-border text-slate-200 text-xs rounded-md px-2 py-1 focus:outline-none focus:border-nexus-cyan font-medium"
          >
            {agentOptions.map((opt) => (
              <option key={opt.id} value={opt.id} className="bg-nexus-surface text-slate-200">
                {opt.name}
              </option>
            ))}
          </select>
        </div>

        <span className="hidden sm:inline text-[11px] text-slate-500 font-mono">
          Press <kbd className="px-1.5 py-0.5 rounded bg-nexus-card border border-nexus-border text-[10px]">Enter</kbd> to send, <kbd className="px-1.5 py-0.5 rounded bg-nexus-card border border-nexus-border text-[10px]">Shift+Enter</kbd> for newline
        </span>
      </div>

      <div className="relative flex items-end rounded-xl border border-nexus-border focus-within:border-nexus-cyan/50 focus-within:shadow-cyan-glow bg-nexus-card/90 transition-all">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Instruct Nexus AI or selected agent..."
          rows={2}
          disabled={disabled}
          className="w-full bg-transparent px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none resize-none font-sans"
        />

        <div className="flex items-center space-x-2 p-2 shrink-0">
          {/* Voice Input Button */}
          <button
            type="button"
            onClick={toggleVoice}
            className={`p-2 rounded-lg border transition-all ${
              isListening
                ? 'bg-nexus-rose/20 border-nexus-rose text-nexus-rose animate-pulse'
                : 'bg-nexus-surface/60 border-nexus-border hover:bg-nexus-surface text-slate-400 hover:text-white'
            }`}
            title={isListening ? 'Listening...' : 'Voice Dictation'}
          >
            {isListening ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
          </button>

          {/* Send Button */}
          <button
            type="submit"
            disabled={!input.trim() || disabled}
            className="p-2 rounded-lg bg-gradient-to-r from-nexus-cyan to-nexus-indigo hover:from-cyan-400 hover:to-indigo-500 text-slate-950 font-bold transition-all disabled:opacity-30 disabled:cursor-not-allowed shadow-sm"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </form>
  );
};
