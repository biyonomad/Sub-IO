
import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';

const PresetSelector = ({ presets, value, onChange, disabled }) => {
  return (
    <div className="space-y-2">
      <Label htmlFor="preset" className="text-sm font-medium text-foreground">
        Subtitle preset
      </Label>
      <Select value={value || 'youtube_standard'} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger id="preset" className="glass-card border-border/50 text-foreground">
          <SelectValue placeholder="Select preset" />
        </SelectTrigger>
        <SelectContent className="glass-card border-border/50">
          {presets.map((preset) => (
            <SelectItem key={preset.value} value={preset.value} className="text-foreground">
              {preset.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};

export default PresetSelector;
