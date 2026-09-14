import React, { useState } from 'react';
import { Settings as SettingsIcon, Key, Shield, Sparkles, Server, Check, Save } from 'lucide-react';
import { request } from '../../services/api';

export const Settings: React.FC = () => {
  const [geminiKey, setGeminiKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [anthropicKey, setAnthropicKey] = useState('');
  const [demoMode, setDemoMode] = useState(true);
  const [autoApproveSafe, setAutoApproveSafe] = useState(true);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await request('/api/system/settings', {
        method: 'POST',
        body: JSON.stringify({
          gemini_api_key: geminiKey || undefined,
          openai_api_key: openaiKey || undefined,
          anthropic_api_key: anthropicKey || undefined,
          demo_mode: demoMode,
          auto_approve_safe_actions: autoApproveSafe,
        }),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error('Failed to update settings', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto px-8 py-8 space-y-8 bg-nexus-bg">
      {/* Header */}
      <div className="border-b border-nexus-border pb-6">
        <div className="flex items-center space-x-2">
          <SettingsIcon className="w-5 h-5 text-nexus-cyan" />
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            System & Provider Configuration
          </h1>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Manage AI providers, human-in-the-loop security boundaries, and runtime execution modes.
        </p>
      </div>

      <form onSubmit={handleSave} className="max-w-3xl space-y-6">
        {/* Demo Mode Banner */}
        <div className="p-4 rounded-2xl bg-gradient-to-r from-nexus-amber/10 to-nexus-violet/10 border border-nexus-amber/30 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs font-bold text-nexus-amber">
              <Sparkles className="w-4 h-4" />
              <span>ZERO-DEPENDENCY DEMO MODE</span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={demoMode}
                onChange={(e) => setDemoMode(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-nexus-card peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-nexus-amber"></div>
            </label>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed font-normal">
            When Demo Mode is enabled or API keys are not entered, Nexus AI operates with complete simulated multi-agent reasoning, simulated tool outputs, and WebSocket streaming without requiring external paid credentials.
          </p>
        </div>

        {/* AI Model API Keys */}
        <div className="glass-panel p-6 rounded-2xl border border-nexus-border space-y-4">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-300">
            <Key className="w-4 h-4 text-nexus-cyan" />
            <span>AI Provider API Credentials (Optional)</span>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">Google Gemini API Key</label>
              <input
                type="password"
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                placeholder="AIzaSy..."
                className="w-full px-3.5 py-2 rounded-xl bg-nexus-surface border border-nexus-border text-xs text-white font-mono placeholder-slate-600 focus:outline-none focus:border-nexus-cyan"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">OpenAI API Key</label>
              <input
                type="password"
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                placeholder="sk-proj-..."
                className="w-full px-3.5 py-2 rounded-xl bg-nexus-surface border border-nexus-border text-xs text-white font-mono placeholder-slate-600 focus:outline-none focus:border-nexus-cyan"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">Anthropic API Key</label>
              <input
                type="password"
                value={anthropicKey}
                onChange={(e) => setAnthropicKey(e.target.value)}
                placeholder="sk-ant-..."
                className="w-full px-3.5 py-2 rounded-xl bg-nexus-surface border border-nexus-border text-xs text-white font-mono placeholder-slate-600 focus:outline-none focus:border-nexus-cyan"
              />
            </div>
          </div>
        </div>

        {/* Security Thresholds */}
        <div className="glass-panel p-6 rounded-2xl border border-nexus-border space-y-4">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-300">
            <Shield className="w-4 h-4 text-nexus-emerald" />
            <span>Security Guardrails & Authorization</span>
          </div>

          <div className="flex items-center justify-between pt-1">
            <div>
              <div className="text-xs font-semibold text-white">Auto-approve safe read actions</div>
              <p className="text-[11px] text-slate-400">File searches, system status, and calculations run autonomously.</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={autoApproveSafe}
                onChange={(e) => setAutoApproveSafe(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-nexus-card peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-nexus-cyan"></div>
            </label>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex items-center space-x-4">
          <button
            type="submit"
            disabled={loading}
            className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-nexus-cyan to-nexus-indigo hover:from-cyan-400 hover:to-indigo-500 text-slate-950 font-bold text-xs shadow-cyan-glow transition-all"
          >
            {saved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
            <span>{saved ? 'Configuration Saved' : 'Apply Configuration'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
