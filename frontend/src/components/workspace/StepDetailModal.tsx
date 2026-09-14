import React from 'react';
import { Modal } from '../ui/Modal';
import { TaskStep } from '../../types';
import { formatDuration, copyToClipboard } from '../../utils/formatters';
import { Copy, Check, Clock, ShieldCheck, Activity } from 'lucide-react';

interface StepDetailModalProps {
  step: TaskStep | null;
  onClose: () => void;
}

export const StepDetailModal: React.FC<StepDetailModalProps> = ({ step, onClose }) => {
  const [copied, setCopied] = React.useState(false);

  if (!step) return null;

  const handleCopy = async () => {
    const text = typeof step.output_data === 'string'
      ? step.output_data
      : JSON.stringify(step.output_data, null, 2);
    const success = await copyToClipboard(text);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const output = step.output_data || {};

  return (
    <Modal
      isOpen={Boolean(step)}
      onClose={onClose}
      title={`${step.agent_name} - Execution Details`}
      subtitle={`Step ${step.step_order} • Status: ${step.status.toUpperCase()}`}
      maxWidth="4xl"
    >
      <div className="space-y-5 text-sm">
        {/* Top Metric Bar */}
        <div className="grid grid-cols-3 gap-3 p-3 bg-slate-900/60 rounded-xl border border-slate-800 text-xs">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-blue-400" />
            <div>
              <div className="text-slate-500 font-mono">EXECUTION TIME</div>
              <div className="font-semibold text-slate-200">{formatDuration(step.duration_seconds)}</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <div>
              <div className="text-slate-500 font-mono">STATUS</div>
              <div className="font-semibold text-slate-200 capitalize">{step.status}</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-purple-400" />
            <div>
              <div className="text-slate-500 font-mono">REVISION CYCLES</div>
              <div className="font-semibold text-slate-200">{step.retry_count || 0} / 2</div>
            </div>
          </div>
        </div>

        {/* Operation Header */}
        {step.operation && (
          <div className="p-3 bg-blue-950/20 border border-blue-500/20 rounded-xl text-blue-300 text-xs flex items-center justify-between">
            <span><strong>Operation:</strong> {step.operation}</span>
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-mono transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              {copied ? 'Copied' : 'Copy Output'}
            </button>
          </div>
        )}

        {/* Specialized Output Views */}
        {/* 1. Data Analyst: Stats & Trends */}
        {step.agent_id === 'data_analyst' && output.statistics && (
          <div className="space-y-4">
            <h4 className="font-semibold text-slate-200 text-xs uppercase tracking-wider font-mono">
              Computed Descriptive Statistics
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left border border-slate-800 rounded-lg overflow-hidden">
                <thead className="bg-slate-900 text-slate-400 font-mono uppercase">
                  <tr>
                    <th className="p-2.5">Metric</th>
                    <th className="p-2.5">Total</th>
                    <th className="p-2.5">Mean</th>
                    <th className="p-2.5">Median</th>
                    <th className="p-2.5">Std Dev</th>
                    <th className="p-2.5">Min / Max</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {Object.entries(output.statistics).map(([metric, s]: [string, any]) => (
                    <tr key={metric} className="hover:bg-slate-900/40">
                      <td className="p-2.5 font-medium text-slate-300">{metric}</td>
                      <td className="p-2.5 font-mono text-blue-300">${s.total ? s.total.toLocaleString() : '-'}</td>
                      <td className="p-2.5 font-mono">{s.mean?.toLocaleString()}</td>
                      <td className="p-2.5 font-mono">{s.median?.toLocaleString()}</td>
                      <td className="p-2.5 font-mono text-slate-400">{s.std}</td>
                      <td className="p-2.5 font-mono text-slate-400">{s.min} / {s.max}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {output.summary && (
              <div className="p-3.5 bg-slate-900/60 rounded-xl border border-slate-800 text-slate-300 text-xs leading-relaxed whitespace-pre-line">
                {output.summary}
              </div>
            )}
          </div>
        )}

        {/* 2. Coding Agent: Code & Optimizations */}
        {step.agent_id === 'coding' && output.code && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span className="font-mono">Language: {output.language || 'Python'}</span>
              <span className="text-amber-400/90 text-[11px]">Command execution requires explicit permission</span>
            </div>
            <pre className="p-4 bg-[#07090e] border border-slate-800 rounded-xl overflow-x-auto text-xs font-mono text-emerald-300 leading-relaxed">
              {output.code}
            </pre>
            {output.explanation && (
              <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/40 p-3 rounded-xl border border-slate-800">
                {output.explanation}
              </p>
            )}
          </div>
        )}

        {/* 3. Risk Agent: Risk Matrix */}
        {step.agent_id === 'risk' && output.risks && (
          <div className="space-y-3">
            <h4 className="font-semibold text-slate-200 text-xs uppercase tracking-wider font-mono">
              Risk Surface Assessment ({output.overall_risk_level} Risk Level)
            </h4>
            <div className="space-y-2">
              {output.risks.map((r: any, i: number) => (
                <div key={i} className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xs text-slate-200">{r.title}</span>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                      r.severity === 'Critical' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
                      r.severity === 'High' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                      'bg-blue-500/10 text-blue-400 border-blue-500/20'
                    }`}>
                      {r.severity} Severity
                    </span>
                  </div>
                  {r.impact && <p className="text-xs text-slate-400">{r.impact}</p>}
                  <p className="text-xs text-emerald-400/90 font-mono"><strong>Mitigation:</strong> {r.mitigation}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 4. Reviewer Agent: Audit Scores & Checks */}
        {step.agent_id === 'reviewer' && output.audit_checks && (
          <div className="space-y-3">
            <div className="p-3 bg-emerald-950/20 border border-emerald-500/20 rounded-xl text-emerald-300 text-xs">
              <strong>Quality Audit Result:</strong> {output.approved ? 'APPROVED ✓' : 'REWORK NEEDED'} (Confidence: {Math.round((output.confidence || 1) * 100)}%)
            </div>
            <div className="space-y-1.5">
              {output.audit_checks.map((chk: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-2.5 bg-slate-900/40 rounded-lg border border-slate-800 text-xs">
                  <span className="text-slate-300">{chk.check}</span>
                  <span className="text-emerald-400 font-mono font-medium">PASSED</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Fallback JSON payload viewer */}
        <div className="pt-2">
          <details className="text-xs text-slate-500">
            <summary className="cursor-pointer hover:text-slate-400 font-mono">View Raw Payload JSON</summary>
            <pre className="mt-2 p-3 bg-slate-950 border border-slate-800 rounded-lg overflow-x-auto text-[11px] font-mono text-slate-400">
              {JSON.stringify(step.output_data, null, 2)}
            </pre>
          </details>
        </div>
      </div>
    </Modal>
  );
};
