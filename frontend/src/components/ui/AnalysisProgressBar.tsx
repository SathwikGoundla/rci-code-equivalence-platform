import React, { useEffect, useState } from 'react';
import { CheckCircle2 } from 'lucide-react';

const STEPS = [
  { id: 'upload',   label: 'Uploading Files' },
  { id: 'c_parse',  label: 'Parsing C' },
  { id: 'f_parse',  label: 'Parsing Fortran' },
  { id: 'ir',       label: 'IR Generation' },
  { id: 'compare',  label: 'Comparison' },
  { id: 'gaps',     label: 'Gap Detection' },
] as const;

const STEP_DURATION_MS = 1_100; // how long each step stays "active"

interface AnalysisProgressBarProps {
  active: boolean; // true = analysis in flight
}

export const AnalysisProgressBar: React.FC<AnalysisProgressBarProps> = ({ active }) => {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    if (!active) {
      setCurrentStep(0);
      return;
    }

    // Animate through steps
    setCurrentStep(0);
    const timers: ReturnType<typeof setTimeout>[] = [];

    STEPS.forEach((_, i) => {
      const t = setTimeout(() => {
        setCurrentStep(i);
      }, i * STEP_DURATION_MS);
      timers.push(t);
    });

    return () => timers.forEach(clearTimeout);
  }, [active]);

  if (!active) return null;

  return (
    <div className="analysis-progress" role="status" aria-label="Analysis in progress">
      <div className="analysis-progress-label">
        <div className="spinner" style={{ width: 12, height: 12, borderWidth: 2 }} />
        <span>Analyzing…</span>
      </div>
      <div className="analysis-progress-steps">
        {STEPS.map((step, i) => {
          const isDone   = i < currentStep;
          const isActive = i === currentStep;
          return (
            <div
              key={step.id}
              className={[
                'progress-step',
                isDone   ? 'done'   : '',
                isActive ? 'active' : '',
              ].filter(Boolean).join(' ')}
            >
              <div className="progress-step-dot">
                {isDone && <CheckCircle2 size={10} />}
              </div>
              <div className="progress-step-label">{step.label}</div>
              {i < STEPS.length - 1 && <div className="progress-step-line" />}
            </div>
          );
        })}
      </div>
    </div>
  );
};
