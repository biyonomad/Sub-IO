
import React, { useState, useEffect } from 'react';
import { Helmet } from 'react-helmet';
import { motion } from 'framer-motion';
import { Sparkles, Coffee, ArrowRight, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Toaster } from '@/components/ui/sonner';
import { toast } from 'sonner';
import { useSubioConfig } from '@/hooks/useSubioConfig.js';
import { useSubioUpload } from '@/hooks/useSubioUpload.js';
import { useSubioTranscription } from '@/hooks/useSubioTranscription.js';
import PlanCard from '@/components/PlanCard.jsx';
import UploadZone from '@/components/UploadZone.jsx';
import LanguageSelector from '@/components/LanguageSelector.jsx';
import PresetSelector from '@/components/PresetSelector.jsx';
import ProgressIndicator from '@/components/ProgressIndicator.jsx';
import ResultsTabs from '@/components/ResultsTabs.jsx';

const SubioApp = () => {
  const [selectedLanguage, setSelectedLanguage] = useState('auto');
  const [selectedPreset, setSelectedPreset] = useState('youtube_standard');
  const [translateOutput, setTranslateOutput] = useState(false);
  const [targetLanguage, setTargetLanguage] = useState('en');

  const { plan, languages, presets, defaultLanguage, defaultPreset, backendOnline, loading: configLoading } = useSubioConfig();
  
  // Sync defaults when config loads
  useEffect(() => {
    if (defaultLanguage) setSelectedLanguage(defaultLanguage);
    if (defaultPreset) setSelectedPreset(defaultPreset);
  }, [defaultLanguage, defaultPreset]);

  const {
    file,
    uploadProgress,
    loading: uploading,
    error: uploadError,
    selectFile,
    uploadFile,
    reset: resetUpload,
  } = useSubioUpload();

  const {
    status: jobStatus,
    progress,
    txtFileId,
    srtFileId,
    txtFilename,
    srtFilename,
    translatedTxtFileId,
    translatedSrtFileId,
    translatedTxtFilename,
    translatedSrtFilename,
    loading: processing,
    error: transcriptionError,
    startTranscription,
    downloadTxt,
    downloadSrt,
    downloadTranslatedTxt,
    downloadTranslatedSrt,
    reset: resetTranscription,
  } = useSubioTranscription();

  const handleGenerate = async () => {
    if (!backendOnline) {
      toast.error('Backend is offline. Cannot start transcription.');
      return;
    }
    
    if (!file) {
      toast('Please select a video file');
      return;
    }

    try {
      const uploadJson = await uploadFile();
      
      if (!uploadJson) {
        return; 
      }

      const uploadId = uploadJson.upload_id;
      if (typeof uploadId !== 'string' || !uploadId.trim()) {
        throw new Error('uploadId must be a non-empty string, got: ' + JSON.stringify(uploadId));
      }

      // Normalize values before calling transcribe
      const language = selectedLanguage || 'auto';
      const presetId = selectedPreset || 'youtube_standard';

      await startTranscription(uploadId, language, presetId, translateOutput, targetLanguage);
    } catch (err) {
      toast.error(err.message || 'An error occurred. Please try again.');
    }
  };

  const handleReset = () => {
    resetUpload();
    resetTranscription();
    setSelectedLanguage(defaultLanguage || 'auto');
    setSelectedPreset(defaultPreset || 'youtube_standard');
  };

  const handleDownloadTxt = async () => {
    try {
      await downloadTxt();
      toast.success('TXT file downloaded');
    } catch (err) {
      toast.error('Failed to download TXT');
    }
  };

  const handleDownloadSrt = async () => {
    try {
      await downloadSrt();
      toast.success('SRT file downloaded');
    } catch (err) {
      toast.error('Failed to download SRT');
    }
  };

  const isProcessing = uploading || processing;
  const isJobDone = jobStatus === 'completed' || jobStatus === 'done';
  const showResults = isJobDone && !!txtFileId && !!srtFileId;
  const showProgress = (uploading || (processing && !isJobDone)) && !showResults;
  const disableUI = !backendOnline || isProcessing || configLoading;

  return (
    <>
      <Helmet>
        <title>Subio - Local Video-to-Text & SRT Subtitle Generator</title>
        <meta name="description" content="Local video-to-text conversion with TXT transcript and SRT subtitle generation." />
      </Helmet>

      <div className="min-h-screen bg-background">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {!configLoading && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-8"
            >
              {backendOnline ? (
                <div className="glass-card rounded-xl p-4 border border-primary/50 bg-primary/10 flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-primary" />
                  <p className="text-sm font-medium text-primary">
                    Backend online
                  </p>
                </div>
              ) : (
                <div className="glass-card rounded-xl p-4 border border-destructive/50 bg-destructive/10 flex items-center gap-3">
                  <AlertCircle className="w-5 h-5 text-destructive" />
                  <p className="text-sm font-medium text-destructive">
                    Backend offline
                  </p>
                </div>
              )}
            </motion.div>
          )}

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="text-center mb-12">
              <div className="inline-flex items-center gap-2 mb-4">
                <div className="w-12 h-12 rounded-2xl gradient-primary flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
                <h1 className="text-4xl md:text-5xl font-bold text-foreground" style={{ letterSpacing: '-0.02em' }}>
                  Subio
                </h1>
              </div>
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto text-balance">
                Clean transcripts and smart subtitles for creators.
              </p>
            </div>
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="lg:col-span-1"
            >
              <PlanCard plan={plan} />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="lg:col-span-2 space-y-6"
            >
              <UploadZone
                file={file}
                onFileSelect={selectFile}
                disabled={disableUI}
              />

              {uploadError && (
                <div className="glass-card rounded-xl p-4 border border-destructive/50 bg-destructive/5">
                  <p className="text-sm text-destructive">{uploadError}</p>
                </div>
              )}

              {transcriptionError && (
                <div className="glass-card rounded-xl p-4 border border-destructive/50 bg-destructive/5">
                  <p className="text-sm text-destructive">{transcriptionError}</p>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <LanguageSelector
                  languages={languages}
                  value={selectedLanguage}
                  onChange={setSelectedLanguage}
                  disabled={disableUI}
                />
                <PresetSelector
                  presets={presets}
                  value={selectedPreset}
                  onChange={setSelectedPreset}
                  disabled={disableUI}
                />
              </div>

              <div className="glass-card rounded-xl p-4 space-y-3">
                <label className="flex items-center gap-3 text-sm font-medium cursor-pointer">
                  <input
                    type="checkbox"
                    checked={translateOutput}
                    onChange={(event) => setTranslateOutput(event.target.checked)}
                    disabled={disableUI}
                    className="h-4 w-4"
                  />
                  <span>Generate translated outputs</span>
                </label>

                {translateOutput && (
                  <div className="space-y-2">
                    <label htmlFor="target-language" className="block text-sm font-medium text-foreground/80">
                      Target language
                    </label>
                    <select
                      id="target-language"
                      value={targetLanguage}
                      onChange={(event) => setTargetLanguage(event.target.value)}
                      disabled={disableUI}
                      className="w-full h-10 rounded-md border border-border bg-background px-3 text-sm"
                    >
                      <option value="en">English</option>
                      <option value="de">German</option>
                      <option value="tr">Turkish</option>
                      <option value="uk">Ukrainian</option>
                    </select>
                  </div>
                )}
              </div>

              <Button
                onClick={handleGenerate}
                disabled={!file || disableUI}
                className="w-full h-12 text-base font-medium gradient-primary hover:opacity-90 transition-all duration-200 active:scale-[0.98]"
              >
                {isProcessing ? 'Processing...' : 'Generate transcript'}
                {!isProcessing && <ArrowRight className="w-5 h-5 ml-2" />}
              </Button>
            </motion.div>
          </div>

          {showProgress && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="mb-8"
            >
              <ProgressIndicator
                status={uploading ? 'uploading' : jobStatus || 'starting'}
                progress={uploading ? `${uploadProgress}%` : progress}
              />
            </motion.div>
          )}

          {showResults && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="space-y-6"
            >
              <ResultsTabs 
                txtFileId={txtFileId}
                srtFileId={srtFileId}
                txtFilename={txtFilename}
                srtFilename={srtFilename}
          translatedTxtFileId={translatedTxtFileId}
          translatedSrtFileId={translatedSrtFileId}
          translatedTxtFilename={translatedTxtFilename}
          translatedSrtFilename={translatedSrtFilename}
                onDownloadTxt={handleDownloadTxt}
                onDownloadSrt={handleDownloadSrt}
                onDownloadTranslatedTxt={downloadTranslatedTxt}
                onDownloadTranslatedSrt={downloadTranslatedSrt}
              />

              <div className="flex justify-center">
                <Button
                  variant="outline"
                  onClick={handleReset}
                  className="gap-2"
                >
                  Process another video
                </Button>
              </div>
            </motion.div>
          )}

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="mt-16 text-center"
          >
            <div className="glass-card rounded-2xl p-8 max-w-2xl mx-auto">
              <Coffee className="w-12 h-12 text-primary mx-auto mb-4" />
              <p className="text-base text-foreground/90 mb-4">
                Subio runs locally on your Mac for personal video transcription.
              </p>
              <Button
                asChild
                className="gradient-secondary hover:opacity-90 transition-all duration-200 active:scale-[0.98]"
              >
                <a
                  href="https://buymeacoffee.com/ilkerkilic"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="gap-2"
                >
                  <Coffee className="w-4 h-4" />
                  Local Subio
                </a>
              </Button>
            </div>
          </motion.div>
        </div>
      </div>

      <Toaster />
    </>
  );
};

export default SubioApp;
