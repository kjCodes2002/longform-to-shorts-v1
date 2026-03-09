import type { PipelineStep } from '../types';

interface ProgressStepperProps {
  currentStep: PipelineStep;
}

const STEPS: { key: PipelineStep; label: string }[] = [
  { key: 'uploading', label: 'Uploading' },
  { key: 'extracting', label: 'Extracting Audio' },
  { key: 'transcribing', label: 'Transcribing' },
  { key: 'highlighting', label: 'Finding Highlights' },
  { key: 'clipping', label: 'Clipping' },
];

const stepOrder = STEPS.map(s => s.key);

function getStepStatus(stepKey: PipelineStep, currentStep: PipelineStep): 'completed' | 'active' | 'pending' {
  const currentIdx = stepOrder.indexOf(currentStep);
  const stepIdx = stepOrder.indexOf(stepKey);

  if (currentStep === 'done') return 'completed';
  if (currentStep === 'error') {
    return stepIdx < currentIdx ? 'completed' : stepIdx === currentIdx ? 'active' : 'pending';
  }
  if (stepIdx < currentIdx) return 'completed';
  if (stepIdx === currentIdx) return 'active';
  return 'pending';
}

export default function ProgressStepper({ currentStep }: ProgressStepperProps) {
  if (currentStep === 'idle') return null;

  return (
    <div className="animate-fade-in">
      <div className="bg-bg-card rounded-2xl border border-border px-6 py-5">
        <div className="flex items-center justify-between">
          {STEPS.map((step, i) => {
            const status = getStepStatus(step.key, currentStep);
            return (
              <div key={step.key} className="flex items-center">
                <div className="flex flex-col items-center gap-2">
                  {/* Circle */}
                  <div className={`
                    w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold
                    transition-all duration-500
                    ${status === 'completed'
                      ? 'bg-emerald text-bg-primary'
                      : status === 'active'
                        ? 'bg-amber text-bg-primary animate-pulse-glow'
                        : 'bg-bg-secondary text-text-muted border border-border'
                    }
                  `}>
                    {status === 'completed' ? (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                      </svg>
                    ) : (
                      i + 1
                    )}
                  </div>
                  {/* Label */}
                  <span className={`
                    text-xs font-medium whitespace-nowrap
                    ${status === 'completed' ? 'text-emerald'
                      : status === 'active' ? 'text-amber'
                        : 'text-text-muted'
                    }
                  `}>
                    {step.label}
                  </span>
                </div>

                {/* Connector line */}
                {i < STEPS.length - 1 && (
                  <div className={`
                    w-12 sm:w-20 h-0.5 mx-2 mb-6
                    transition-colors duration-500
                    ${status === 'completed' ? 'bg-emerald' : 'bg-border'}
                  `} />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
