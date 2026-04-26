
const API_BASE_URL = 'http://localhost:8000/api';

const coreHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    const healthJson = await response.json();
    console.log("Health response:", healthJson);
    return healthJson;
  } catch (error) {
    console.error('Health check error:', error);
    return { status: 'error', isOnline: false };
  }
};

const coreLanguages = async () => {
  const response = await fetch(`${API_BASE_URL}/config/languages`);
  if (!response.ok) throw new Error('Failed to fetch languages');
  const languagesJson = await response.json();
  console.log("Languages response:", languagesJson);
  return Array.isArray(languagesJson) ? languagesJson : (languagesJson.languages || []);
};

const corePresets = async () => {
  const response = await fetch(`${API_BASE_URL}/config/presets`);
  if (!response.ok) throw new Error('Failed to fetch presets');
  const presetsJson = await response.json();
  console.log("Presets response:", presetsJson);
  return Array.isArray(presetsJson) ? presetsJson : (presetsJson.presets || []);
};

const corePlans = async () => {
  const response = await fetch(`${API_BASE_URL}/config/plans`);
  if (!response.ok) throw new Error('Failed to fetch plans');
  const plansJson = await response.json();
  return Array.isArray(plansJson) ? plansJson : (plansJson.plans || plansJson.plan || plansJson);
};

const coreUpload = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  });

  const uploadJson = await response.json();
  console.log("Upload response:", uploadJson);

  if (!response.ok) {
    throw new Error(`Upload failed with status ${response.status}: ${JSON.stringify(uploadJson)}`);
  }

  if (!uploadJson.upload_id) {
    throw new Error('Missing upload_id in upload response: ' + JSON.stringify(uploadJson));
  }

  return {
    upload_id: uploadJson.upload_id,
    filename: uploadJson.filename,
    size_bytes: uploadJson.size_bytes,
    duration_seconds: uploadJson.duration_seconds,
  };
};

const coreTranscribe = async (uploadId, language, presetId, translate = false, targetLanguage = null) => {
  const response = await fetch(`${API_BASE_URL}/transcribe`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      upload_id: uploadId,
      language: language,
      preset_id: presetId,
      translate: Boolean(translate),
      target_language: translate ? targetLanguage : null,
    }),
  });

  const transcribeJson = await response.json();
  console.log("Transcribe response:", transcribeJson);

  if (!response.ok) {
    throw new Error(`Transcribe failed with status ${response.status}: ${JSON.stringify(transcribeJson)}`);
  }

  if (!transcribeJson.job_id) {
    throw new Error('Missing job_id in transcribe response: ' + JSON.stringify(transcribeJson));
  }

  return { job_id: transcribeJson.job_id };
};

const coreJob = async (jobId) => {
  if (!jobId) {
    throw new Error("jobId is required to fetch job status");
  }

  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
  const jobJson = await response.json();
  console.log("Job response:", jobJson);

  if (!response.ok) {
    throw new Error(`Get job failed with status ${response.status}: ${JSON.stringify(jobJson)}`);
  }

  return jobJson;
};

const corePreview = async (fileId) => {
  const response = await fetch(`${API_BASE_URL}/preview/${fileId}`);
  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Get preview failed with status ${response.status}: ${errText}`);
  }
  return await response.text();
};

const coreDownloadUrl = (fileId) => {
  return `${API_BASE_URL}/download/${fileId}`;
};

export const subioApi = {
  // Health aliases
  getHealth: coreHealth,
  health: coreHealth,

  // Languages aliases
  getLanguages: coreLanguages,
  fetchLanguages: coreLanguages,
  loadLanguages: coreLanguages,

  // Presets aliases
  getPresets: corePresets,
  fetchPresets: corePresets,
  loadPresets: corePresets,

  // Plans aliases
  getPlans: corePlans,
  fetchPlans: corePlans,
  loadPlans: corePlans,

  // Upload aliases
  upload: coreUpload,
  uploadVideo: coreUpload,
  uploadFile: coreUpload,

  // Transcribe aliases
  transcribe: coreTranscribe,
  startTranscription: coreTranscribe,
  generateTranscript: coreTranscribe,

  // Job aliases
  getJob: coreJob,
  getJobStatus: coreJob,
  pollJob: coreJob,

  // Preview aliases
  preview: corePreview,
  getPreview: corePreview,
  previewFile: corePreview,

  // Download aliases
  downloadUrl: coreDownloadUrl,
  getDownloadUrl: coreDownloadUrl,
};

export default subioApi;
