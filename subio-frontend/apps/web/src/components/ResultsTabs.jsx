import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Copy, Download, Eye, FileText, Subtitles, Languages } from 'lucide-react';
import { toast } from 'sonner';
import PreviewModal from '@/components/PreviewModal.jsx';
import { subioApi } from '@/lib/subioApi.js';

const OutputCard = ({
  icon: Icon,
  title,
  filename,
  fallbackFilename,
  fileId,
  format,
  copyLabel,
  previewTitle,
  onDownload,
  loadingPreview,
  onPreview,
  onCopy,
}) => {
  if (!fileId) return null;

  return (
    <div className="glass-card rounded-2xl p-6 flex flex-col h-full shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
            <Icon className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">{title}</h3>
            <p className="text-sm text-muted-foreground">{filename || fallbackFilename}</p>
          </div>
        </div>
      </div>

      <div className="mt-auto flex flex-col gap-3">
        <Button
          variant="outline"
          onClick={() => onPreview(fileId, previewTitle, format)}
          disabled={loadingPreview === fileId}
          className="w-full gap-2 transition-all duration-200 active:scale-[0.98]"
        >
          <Eye className="w-4 h-4" />
          {loadingPreview === fileId ? 'Loading...' : 'Preview'}
        </Button>

        <div className="grid grid-cols-2 gap-3">
          <Button
            variant="secondary"
            onClick={() => onCopy(fileId, copyLabel)}
            disabled={loadingPreview === fileId}
            className="w-full gap-2 transition-all duration-200 active:scale-[0.98]"
          >
            <Copy className="w-4 h-4" />
            Copy All
          </Button>

          <Button
            onClick={onDownload}
            className="w-full gap-2 transition-all duration-200 active:scale-[0.98]"
          >
            <Download className="w-4 h-4" />
            Download
          </Button>
        </div>
      </div>
    </div>
  );
};

const ResultsTabs = ({
  txtFileId,
  srtFileId,
  txtFilename,
  srtFilename,
  translatedTxtFileId,
  translatedSrtFileId,
  translatedTxtFilename,
  translatedSrtFilename,
  onDownloadTxt,
  onDownloadSrt,
  onDownloadTranslatedTxt,
  onDownloadTranslatedSrt,
}) => {
  const [previewModal, setPreviewModal] = useState({ isOpen: false, content: '', title: '', format: '' });
  const [loadingPreview, setLoadingPreview] = useState(null);

  const handleCopy = async (fileId, label) => {
    try {
      setLoadingPreview(fileId);
      const content = await subioApi.preview(fileId);
      if (!content) {
        toast.error(`No content found for ${label}`);
        return;
      }
      await navigator.clipboard.writeText(content);
      toast.success(`${label} copied to clipboard`);
    } catch (err) {
      toast.error(`Failed to copy ${label}`);
      console.error(err);
    } finally {
      setLoadingPreview(null);
    }
  };

  const handlePreview = async (fileId, title, format) => {
    try {
      setLoadingPreview(fileId);
      const content = await subioApi.preview(fileId);
      setPreviewModal({ isOpen: true, content, title, format });
    } catch (err) {
      toast.error(`Failed to load preview for ${title}`);
      console.error(err);
    } finally {
      setLoadingPreview(null);
    }
  };

  const handleDownloadFromModal = async () => {
    try {
      if (previewModal.format === 'translated_srt') {
        await onDownloadTranslatedSrt?.();
      } else if (previewModal.format === 'translated_txt') {
        await onDownloadTranslatedTxt?.();
      } else if (previewModal.format === 'srt') {
        await onDownloadSrt?.();
      } else {
        await onDownloadTxt?.();
      }
    } catch (err) {
      toast.error('Failed to download file');
    }
    setPreviewModal({ isOpen: false, content: '', title: '', format: '' });
  };

  if (!txtFileId || !srtFileId) {
    return (
      <div className="glass-card rounded-xl p-4 border border-destructive/50 bg-destructive/10">
        <p className="text-sm text-destructive">Output files are missing or invalid.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <OutputCard
          icon={FileText}
          title="Raw Transcript"
          filename={txtFilename}
          fallbackFilename="transcript.txt"
          fileId={txtFileId}
          format="txt"
          copyLabel="Transcript"
          previewTitle="Raw Transcript"
          onDownload={onDownloadTxt}
          loadingPreview={loadingPreview}
          onPreview={handlePreview}
          onCopy={handleCopy}
        />

        <OutputCard
          icon={Subtitles}
          title="SRT Subtitles"
          filename={srtFilename}
          fallbackFilename="subtitles.srt"
          fileId={srtFileId}
          format="srt"
          copyLabel="SRT"
          previewTitle="SRT Subtitles"
          onDownload={onDownloadSrt}
          loadingPreview={loadingPreview}
          onPreview={handlePreview}
          onCopy={handleCopy}
        />

        <OutputCard
          icon={Languages}
          title="Translated Transcript"
          filename={translatedTxtFilename}
          fallbackFilename="translated-transcript.txt"
          fileId={translatedTxtFileId}
          format="translated_txt"
          copyLabel="Translated transcript"
          previewTitle="Translated Transcript"
          onDownload={onDownloadTranslatedTxt}
          loadingPreview={loadingPreview}
          onPreview={handlePreview}
          onCopy={handleCopy}
        />

        <OutputCard
          icon={Languages}
          title="Translated SRT Subtitles"
          filename={translatedSrtFilename}
          fallbackFilename="translated-subtitles.srt"
          fileId={translatedSrtFileId}
          format="translated_srt"
          copyLabel="Translated SRT"
          previewTitle="Translated SRT Subtitles"
          onDownload={onDownloadTranslatedSrt}
          loadingPreview={loadingPreview}
          onPreview={handlePreview}
          onCopy={handleCopy}
        />
      </div>

      <PreviewModal
        isOpen={previewModal.isOpen}
        onClose={() => setPreviewModal({ isOpen: false, content: '', title: '', format: '' })}
        content={previewModal.content}
        title={previewModal.title}
        format={previewModal.format}
        onDownload={handleDownloadFromModal}
      />
    </div>
  );
};

export default ResultsTabs;
