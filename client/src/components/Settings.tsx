import type { PipelineSettings } from '../types';

interface SettingsProps {
  settings: PipelineSettings;
  onChange: (settings: PipelineSettings) => void;
  onProcess: () => void;
  disabled?: boolean;
  hasFile: boolean;
}

export default function Settings({ settings, onChange, onProcess, disabled, hasFile }: SettingsProps) {
  return (
    <div className="bg-bg-card rounded-2xl border border-border p-6 space-y-5">
      {/* Highlights count */}
      <div>
        <div className="flex justify-between items-center mb-2">
          <label className="text-text-secondary text-sm font-medium">Highlights</label>
          <span className="text-emerald font-semibold text-sm tabular-nums">{settings.nAnswers}</span>
        </div>
        <input
          type="range"
          min={1}
          max={5}
          step={1}
          value={settings.nAnswers}
          onChange={(e) => onChange({ ...settings, nAnswers: parseInt(e.target.value) })}
          disabled={disabled}
          className="w-full"
        />
      </div>

      {/* Model */}
      <div>
        <label className="text-text-secondary text-sm font-medium block mb-2">Model</label>
        <select
          value={settings.model}
          onChange={(e) => onChange({ ...settings, model: e.target.value })}
          disabled={disabled}
          className="w-full bg-bg-secondary border border-border rounded-xl px-4 py-2.5 text-text-primary text-sm
                     focus:outline-none focus:border-emerald/50 transition-colors cursor-pointer
                     disabled:opacity-50"
        >
          <option value="gpt-4o-mini">GPT-4o Mini</option>
          <option value="gpt-4o">GPT-4o</option>
        </select>
      </div>

      {/* Temperature */}
      <div>
        <div className="flex justify-between items-center mb-2">
          <label className="text-text-secondary text-sm font-medium">Temperature</label>
          <span className="text-amber font-semibold text-sm tabular-nums">{settings.temperature.toFixed(1)}</span>
        </div>
        <input
          type="range"
          min={0}
          max={2}
          step={0.1}
          value={settings.temperature}
          onChange={(e) => onChange({ ...settings, temperature: parseFloat(e.target.value) })}
          disabled={disabled}
          className="w-full"
        />
      </div>

      {/* Process button */}
      <button
        onClick={onProcess}
        disabled={disabled || !hasFile}
        className={`
          w-full py-3 rounded-xl font-semibold text-sm tracking-wide
          transition-all duration-300
          ${disabled || !hasFile
            ? 'bg-border text-text-muted cursor-not-allowed'
            : 'bg-emerald hover:bg-emerald-light text-bg-primary cursor-pointer shadow-lg hover:shadow-emerald/20 active:scale-[0.98]'
          }
        `}
      >
        {disabled ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Processing...
          </span>
        ) : (
          'Process Video'
        )}
      </button>
    </div>
  );
}
