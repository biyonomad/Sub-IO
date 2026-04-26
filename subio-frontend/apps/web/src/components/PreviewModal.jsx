
import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Copy, Download, X } from 'lucide-react';
import { toast } from 'sonner';

const PreviewModal = ({ isOpen, onClose, content, title, format, onDownload }) => {
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      toast('Copied to clipboard');
    } catch (err) {
      toast('Failed to copy');
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="glass-card max-w-3xl max-h-[80vh] flex flex-col text-foreground">
        <DialogHeader>
          <DialogTitle className="text-foreground">{title}</DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto">
          <pre className={`text-sm whitespace-pre-wrap break-words p-4 rounded-xl bg-muted/50 ${
            format === 'srt' ? 'font-mono' : ''
          }`}>
            {content}
          </pre>
        </div>

        <DialogFooter className="flex gap-2 sm:gap-2">
          <Button variant="outline" onClick={handleCopy} className="gap-2">
            <Copy className="w-4 h-4" />
            Copy all
          </Button>
          <Button onClick={onDownload} className="gap-2">
            <Download className="w-4 h-4" />
            Download
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default PreviewModal;
