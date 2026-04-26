
import { useState } from 'react';
import { subioApi } from '@/lib/subioApi.js';

export const useSubioUpload = () => {
  const [file, setFile] = useState(null);
  const [uploadId, setUploadId] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const validateFile = (selectedFile) => {
    const validTypes = [
      'video/mp4',
      'video/mpeg',
      'video/quicktime',
      'video/x-msvideo',
      'video/x-matroska',
      'video/webm',
    ];

    if (!validTypes.includes(selectedFile.type) && !selectedFile.name.match(/\.(mp4|mpeg|mov|avi|mkv|webm)$/i)) {
      throw new Error('Invalid file type. Please upload a supported video file.');
    }

    const maxSize = 50 * 1024 * 1024 * 1024; // 50 GB
    if (selectedFile.size > maxSize) {
      throw new Error('File size exceeds 50 GB limit.');
    }

    return true;
  };

  const selectFile = (selectedFile) => {
    try {
      if (!selectedFile) {
        setFile(null);
        return;
      }
      validateFile(selectedFile);
      setFile(selectedFile);
      setError(null);
      setUploadProgress(0);
      setUploadId(null);
      setJobId(null);
      setJobStatus(null);
    } catch (err) {
      setError(err.message);
      setFile(null);
    }
  };

  const uploadFile = async () => {
    if (!file) {
      setError('No file selected');
      return null;
    }

    try {
      setLoading(true);
      setError(null);
      setUploadProgress(0);

      // (1) Call subioApi.uploadVideo(file) and store the full response as uploadJson
      const uploadJson = await subioApi.uploadVideo(file);
      
      // (3) Add console.log('Upload response:', uploadJson) for debugging
      console.log('Upload response:', uploadJson);

      // (2) Extract uploadId = uploadJson.upload_id with validation
      const extractedUploadId = uploadJson.upload_id;
      if (typeof extractedUploadId !== 'string' || !extractedUploadId.trim()) {
        throw new Error('uploadId must be a non-empty string, got: ' + JSON.stringify(extractedUploadId));
      }

      setUploadId(extractedUploadId);
      return uploadJson;
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message || 'Upload failed due to network error');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const startTranscription = async (language, preset) => {
    const targetUploadId = uploadId;
    if (!targetUploadId) {
      setError('No upload_id available. Please upload a file first.');
      return null;
    }

    try {
      setLoading(true);
      setError(null);

      const returnedJobId = await subioApi.startTranscription(targetUploadId, language, preset);
      
      setJobId(returnedJobId);
      pollJobStatus(returnedJobId);

      return returnedJobId;
    } catch (err) {
      console.error('Start transcription error:', err);
      setError(err.message || 'Failed to start transcription');
      return null;
    } finally {
      setLoading(false);
    }
  };

  const pollJobStatus = async (currentJobId) => {
    if (!currentJobId) return;

    try {
      const status = await subioApi.getJob(currentJobId);
      setJobStatus(status);
    } catch (err) {
      console.error('Polling error:', err);
      setError(err.message || 'Failed to poll job status');
    }
  };

  const reset = () => {
    setFile(null);
    setUploadProgress(0);
    setLoading(false);
    setUploadId(null);
    setJobId(null);
    setJobStatus(null);
    setError(null);
  };

  return {
    file,
    uploadId,
    jobId,
    jobStatus,
    uploadProgress,
    loading,
    error,
    selectFile,
    uploadFile,
    startTranscription,
    pollJobStatus,
    reset,
  };
};
