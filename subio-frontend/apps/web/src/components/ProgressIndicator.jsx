
import React from 'react';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';

const ProgressIndicator = ({ status, progress }) => {
  const getStatusInfo = () => {
    const statusMap = {
      uploading: { label: 'Uploading', icon: Loader2, color: 'text-primary' },
      probing: { label: 'Probing media', icon: Loader2, color: 'text-primary' },
      extracting: { label: 'Extracting audio', icon: Loader2, color: 'text-primary' },
      transcribing: { label: 'Transcribing', icon: Loader2, color: 'text-primary' },
      formatting: { label: 'Formatting subtitles', icon: Loader2, color: 'text-primary' },
      completed: { label: 'Completed', icon: CheckCircle2, color: 'text-green-500' },
      failed: { label: 'Failed', icon: XCircle, color: 'text-destructive' },
    };

    return statusMap[status] || statusMap.transcribing;
  };

  const statusInfo = getStatusInfo();
  const Icon = statusInfo.icon;

  const steps = [
    { key: 'uploading', label: 'Upload' },
    { key: 'probing', label: 'Probe' },
    { key: 'extracting', label: 'Extract' },
    { key: 'transcribing', label: 'Transcribe' },
    { key: 'formatting', label: 'Format' },
  ];

  const currentStepIndex = steps.findIndex(step => step.key === status);

  return (
    <div className="glass-card rounded-2xl p-6 space-y-4">
      <div className="flex items-center gap-3">
        <Icon className={`w-6 h-6 ${statusInfo.color} ${status !== 'completed' && status !== 'failed' ? 'animate-spin' : ''}`} />
        <div className="flex-1">
          <p className="text-sm font-medium text-foreground">{statusInfo.label}</p>
          {progress && typeof progress === 'string' && (
            <p className="text-xs text-muted-foreground">{progress}</p>
          )}
        </div>
      </div>

      {status !== 'completed' && status !== 'failed' && (
        <div className="flex gap-2">
          {steps.map((step, index) => (
            <div
              key={step.key}
              className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${
                index <= currentStepIndex
                  ? 'bg-primary'
                  : 'bg-muted'
              }`}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default ProgressIndicator;
