import { useState } from 'react';
import { subioApi } from '../lib/subioApi';

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export const useSubioTranscription = () => {
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(null);

  const [txtFileId, setTxtFileId] = useState(null);
  const [srtFileId, setSrtFileId] = useState(null);
  const [txtFilename, setTxtFilename] = useState('');
  const [srtFilename, setSrtFilename] = useState('');

  const [translatedTxtFileId, setTranslatedTxtFileId] = useState(null);
  const [translatedSrtFileId, setTranslatedSrtFileId] = useState(null);
  const [translatedTxtFilename, setTranslatedTxtFilename] = useState('');
  const [translatedSrtFilename, setTranslatedSrtFilename] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const clearOutputs = () => {
    setTxtFileId(null);
    setSrtFileId(null);
    setTxtFilename('');
    setSrtFilename('');
    setTranslatedTxtFileId(null);
    setTranslatedSrtFileId(null);
    setTranslatedTxtFilename('');
    setTranslatedSrtFilename('');
  };

  const applyOutputs = (outputs = {}) => {
    if (outputs.txt?.file_id) {
      setTxtFileId(outputs.txt.file_id);
      setTxtFilename(outputs.txt.filename || 'transcript.txt');
    }

    if (outputs.srt?.file_id) {
      setSrtFileId(outputs.srt.file_id);
      setSrtFilename(outputs.srt.filename || 'subtitles.srt');
    }

    if (outputs.translated_txt?.file_id) {
      setTranslatedTxtFileId(outputs.translated_txt.file_id);
      setTranslatedTxtFilename(outputs.translated_txt.filename || 'translated-transcript.txt');
    }

    if (outputs.translated_srt?.file_id) {
      setTranslatedSrtFileId(outputs.translated_srt.file_id);
      setTranslatedSrtFilename(outputs.translated_srt.filename || 'translated-subtitles.srt');
    }
  };

  const pollJobUntilDone = async (nextJobId) => {
    for (;;) {
      const job = await subioApi.getJobStatus(nextJobId);

      setStatus(job.status || null);
      setProgress(job.progress ?? null);

      if (job.error) {
        throw new Error(job.error);
      }

      const isDone =
        job.status === 'done' ||
        job.status === 'completed' ||
        job.status === 'success' ||
        job.progress === 1 ||
        job.progress === 1.0 ||
        job.progress === 100;

      if (isDone) {
        applyOutputs(job.outputs || {});
        setLoading(false);
        return job;
      }

      if (job.status === 'failed' || job.status === 'error') {
        throw new Error(job.error || 'Transcription failed');
      }

      await sleep(1500);
    }
  };

  const startTranscription = async (
    uploadId,
    language = 'auto',
    preset = 'youtube_standard',
    translate = false,
    targetLanguage = 'en'
  ) => {
    try {
      setLoading(true);
      setError(null);
      clearOutputs();
      setStatus('starting');
      setProgress(null);

      const response = await subioApi.startTranscription(
        uploadId,
        language || 'auto',
        preset || 'youtube_standard',
        Boolean(translate),
        translate ? targetLanguage : null
      );

      const nextJobId = response.job_id;
      setJobId(nextJobId);

      return await pollJobUntilDone(nextJobId);
    } catch (err) {
      console.error('Transcription error:', err);
      setError(err.message || 'Transcription failed');
      setLoading(false);
      throw err;
    }
  };

  const downloadFile = (fileId) => {
    if (!fileId) return;
    window.open(subioApi.downloadUrl(fileId), '_blank', 'noopener,noreferrer');
  };

  const downloadTxt = () => downloadFile(txtFileId);
  const downloadSrt = () => downloadFile(srtFileId);
  const downloadTranslatedTxt = () => downloadFile(translatedTxtFileId);
  const downloadTranslatedSrt = () => downloadFile(translatedSrtFileId);

  const reset = () => {
    setJobId(null);
    setStatus(null);
    setProgress(null);
    clearOutputs();
    setError(null);
    setLoading(false);
  };

  return {
    jobId,
    status,
    progress,

    txtFileId,
    srtFileId,
    txtFilename,
    srtFilename,

    translatedTxtFileId,
    translatedSrtFileId,
    translatedTxtFilename,
    translatedSrtFilename,

    loading,
    error,

    startTranscription,

    downloadTxt,
    downloadSrt,
    downloadTranslatedTxt,
    downloadTranslatedSrt,

    reset,
  };
};
