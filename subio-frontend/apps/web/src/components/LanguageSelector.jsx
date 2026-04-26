
import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';

const LanguageSelector = ({ languages, value, onChange, disabled }) => {
  return (
    <div className="space-y-2">
      <Label htmlFor="language" className="text-sm font-medium text-foreground">
        Source language
      </Label>
      <Select value={value || 'auto'} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger id="language" className="glass-card border-border/50 text-foreground">
          <SelectValue placeholder="Select language" />
        </SelectTrigger>
        <SelectContent className="glass-card border-border/50">
          {languages.map((lang) => (
            <SelectItem key={lang.value} value={lang.value} className="text-foreground">
              {lang.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};

export default LanguageSelector;
