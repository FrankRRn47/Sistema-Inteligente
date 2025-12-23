import { useEffect, useMemo, useState } from 'react';

import { API_BASE_URL } from '../services/api.js';
import { fetchMediaSnapshot } from '../services/mediaService.js';

const API_ROOT = API_BASE_URL.replace(/\/$/, '');

function buildAbsoluteUrl(path) {
  if (!path) {
    return null;
  }
  if (path.startsWith('http')) {
    return path;
  }
  if (path.startsWith('/')) {
    return `${API_ROOT}${path}`;
  }
  return `${API_ROOT}/${path}`;
}

export default function useSnapshotPreview(snapshotPath) {
  const [previewUrl, setPreviewUrl] = useState(null);
  const [state, setState] = useState(snapshotPath ? 'loading' : 'idle');
  const fallbackUrl = useMemo(() => buildAbsoluteUrl(snapshotPath), [snapshotPath]);

  useEffect(() => {
    let isMounted = true;
    let objectUrl = null;

    if (!snapshotPath) {
      setPreviewUrl(null);
      setState('idle');
      return () => {};
    }

    setState('loading');
    fetchMediaSnapshot(snapshotPath)
      .then((blob) => {
        if (!blob || !isMounted) {
          return;
        }
        objectUrl = URL.createObjectURL(blob);
        setPreviewUrl(objectUrl);
        setState('ready');
      })
      .catch(() => {
        if (isMounted) {
          setState('error');
        }
      });

    return () => {
      isMounted = false;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [snapshotPath]);

  return { previewUrl, fallbackUrl, state };
}
