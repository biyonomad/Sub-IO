
import { useState, useEffect } from 'react';
import { subioApi } from '@/lib/subioApi.js';

export const useSubioConfig = () => {
  const [plan, setPlan] = useState({
    maxUpload: '50GB',
    maxDuration: '2 hours',
    outputs: ['TXT', 'SRT'],
    requiresAuth: false,
    requiresPayment: false,
  });
  const [languages, setLanguages] = useState([]);
  const [presets, setPresets] = useState([]);
  const [defaultLanguage, setDefaultLanguage] = useState('auto');
  const [defaultPreset, setDefaultPreset] = useState('youtube_standard');
  const [backendOnline, setBackendOnline] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        setLoading(true);
        setError(null);

        // Check health first
        const healthRes = await subioApi.getHealth();
        const isOnline = healthRes?.status === 'ok' || healthRes?.isOnline !== false;
        setBackendOnline(isOnline);

        if (!isOnline) {
          throw new Error('Backend offline or unreachable.');
        }

        const [languagesData, presetsData, planData] = await Promise.all([
          subioApi.getLanguages(),
          subioApi.getPresets(),
          subioApi.getPlans(),
        ]);

        // Map languages to ensure consistent value/label for dropdowns
        const rawLanguages = Array.isArray(languagesData) ? languagesData : (languagesData?.languages || []);
        const mappedLanguages = rawLanguages.map(item => ({
          ...item,
          value: item.code || item.value || item.id,
          label: item.label || item.name || item.code
        }));

        // Map presets to ensure consistent value/label for dropdowns
        const rawPresets = Array.isArray(presetsData) ? presetsData : (presetsData?.presets || []);
        const mappedPresets = rawPresets.map(item => ({
          ...item,
          value: item.id || item.value,
          label: item.name || item.label || item.id
        }));

        setLanguages(mappedLanguages);
        setPresets(mappedPresets);
        
        if (planData) {
          setPlan(planData);
        }

        // Merge defaults with response data if provided by the API
        if (languagesData?.default) {
          setDefaultLanguage(languagesData.default);
        }
        if (presetsData?.default) {
          setDefaultPreset(presetsData.default);
        }
        
      } catch (err) {
        console.error('Failed to fetch config or backend offline:', err);
        setBackendOnline(false);
        setError('Backend offline or unreachable.');
        
        // Fallback data so the UI doesn't completely crash if offline
        setLanguages([
          { value: 'auto', label: 'Auto Detect' },
          { value: 'en', label: 'English' },
        ]);
        setPresets([
          { value: 'youtube_standard', label: 'YouTube Standard' },
        ]);
        setDefaultLanguage('auto');
        setDefaultPreset('youtube_standard');
      } finally {
        setLoading(false);
      }
    };

    fetchConfig();
  }, []);

  return {
    plan,
    languages,
    presets,
    defaultLanguage,
    defaultPreset,
    backendOnline,
    loading,
    error,
  };
};
