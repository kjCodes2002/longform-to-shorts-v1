import { useState, useCallback } from 'react';
import UploadZone from './components/UploadZone';
import Settings from './components/Settings';
import ProgressStepper from './components/ProgressStepper';
import ResultsGrid from './components/ResultsGrid';
import { processVideo } from './api/processVideo';
import type { PipelineSettings, PipelineStep, ClipResult } from './types';

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [settings, setSettings] = useState<PipelineSettings>({
    nAnswers: 1,
    model: 'gpt-4o-mini',
    temperature: 0.7,
  });
  const [currentStep, setCurrentStep] = useState<PipelineStep>('idle');
  const [clips, setClips] = useState<ClipResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  const isProcessing = !['idle', 'done', 'error'].includes(currentStep);

  const handleProcess = useCallback(async () => {
    if (!file) return;

    setError(null);
    setClips([]);
    setCurrentStep('uploading');

    // Simulate progress steps since the API is synchronous
    const stepTimers: ReturnType<typeof setTimeout>[] = [];
    const simulateSteps = () => {
      stepTimers.push(setTimeout(() => setCurrentStep('extracting'), 2000));
      stepTimers.push(setTimeout(() => setCurrentStep('transcribing'), 5000));
      stepTimers.push(setTimeout(() => setCurrentStep('highlighting'), 15000));
      stepTimers.push(setTimeout(() => setCurrentStep('clipping'), 25000));
    };

    simulateSteps();

    try {
      const result = await processVideo(file, settings);
      stepTimers.forEach(clearTimeout);

      if (result.status === 'ok' && result.clips.length > 0) {
        setClips(result.clips);
        setCurrentStep('done');
      } else {
        setError(result.errors?.join(', ') || 'No clips were generated');
        setCurrentStep('error');
      }
    } catch (err) {
      stepTimers.forEach(clearTimeout);
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
      setCurrentStep('error');
    }
  }, [file, settings]);

  const handleReset = useCallback(() => {
    setFile(null);
    setClips([]);
    setCurrentStep('idle');
    setError(null);
  }, []);

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Header */}
      <header className="border-b border-border">
        <div className="max-w-6xl mx-auto px-6 py-6">
          <h1 className="text-3xl font-bold tracking-tight">
            Longform <span className="text-emerald">→</span> Shorts
          </h1>
          <p className="text-text-muted text-sm mt-1">AI-powered video highlights</p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Progress stepper */}
        {currentStep !== 'idle' && (
          <div className="mb-8">
            <ProgressStepper currentStep={currentStep} />
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="mb-6 bg-red-500/10 border border-red-500/20 rounded-xl px-5 py-4 animate-fade-in">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-red-400 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
              </svg>
              <div>
                <p className="text-red-400 font-medium text-sm">Processing failed</p>
                <p className="text-red-400/70 text-sm mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Done banner */}
        {currentStep === 'done' && clips.length > 0 && (
          <div className="mb-6 bg-emerald/10 border border-emerald/20 rounded-xl px-5 py-4 flex items-center justify-between animate-fade-in">
            <div className="flex items-center gap-3">
              <svg className="w-5 h-5 text-emerald" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
              </svg>
              <p className="text-emerald font-medium text-sm">
                {clips.length} clip{clips.length > 1 ? 's' : ''} generated successfully!
              </p>
            </div>
            <button
              onClick={handleReset}
              className="text-emerald/70 hover:text-emerald text-sm font-medium transition-colors cursor-pointer"
            >
              Process another
            </button>
          </div>
        )}

        {/* Main content grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left column — Upload + Settings */}
          <div className="lg:col-span-4 space-y-6">
            <UploadZone
              onFileSelect={setFile}
              selectedFile={file}
              disabled={isProcessing}
            />
            <Settings
              settings={settings}
              onChange={setSettings}
              onProcess={handleProcess}
              disabled={isProcessing}
              hasFile={!!file}
            />
          </div>

          {/* Right column — Results */}
          <div className="lg:col-span-8">
            <h2 className="text-lg font-semibold text-text-primary mb-4">Generated Clips</h2>
            <ResultsGrid clips={clips} />
          </div>
        </div>
      </main>
    </div>
  );
}
