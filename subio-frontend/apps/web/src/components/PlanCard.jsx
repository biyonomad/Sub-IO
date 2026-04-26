
import React from 'react';
import { Check } from 'lucide-react';

const PlanCard = ({ plan }) => {
  const features = [
    `${plan?.maxUpload || '50GB'} max upload size`,
    `${plan?.maxDuration || '2 hours'} max duration`,
    `${plan?.outputs?.join(' + ') || 'TXT + SRT'} outputs`,
    plan?.requiresAuth ? 'Account required' : 'No account required',
    plan?.requiresPayment ? 'Payment required' : 'No payment required',
  ];

  return (
    <div className="glass-card rounded-2xl p-6 border border-primary/20">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
          <span className="text-2xl font-bold text-primary">F</span>
        </div>
        <div>
          <h3 className="text-xl font-semibold text-foreground">Local Mode</h3>
          <p className="text-sm text-muted-foreground">No limits, no strings</p>
        </div>
      </div>
      
      <ul className="space-y-3">
        {features.map((feature, index) => (
          <li key={index} className="flex items-start gap-3">
            <Check className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
            <span className="text-sm text-foreground/90">{feature}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default PlanCard;
