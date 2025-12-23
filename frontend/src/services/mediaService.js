import api, { API_BASE_URL } from './api.js';

function normalizeFileEndpoint(pathOrUrl) {
  if (!pathOrUrl) {
    return null;
  }
  const withoutBase = pathOrUrl.startsWith('http')
    ? pathOrUrl.replace(API_BASE_URL, '')
    : pathOrUrl;
  if (withoutBase.startsWith('/media/files')) {
    return withoutBase;
  }
  const sanitized = withoutBase.replace(/^\/+/, '');
  return `/media/files/${sanitized}`;
}

function normalizeAnalysesPayload(data = {}) {
  const analyses = Array.isArray(data.analyses)
    ? data.analyses
    : data.analysis
    ? [data.analysis]
    : [];
  const normalized = { ...data, analyses };
  if (!normalized.analysis && analyses.length > 0) {
    normalized.analysis = analyses[0];
  }
  return normalized;
}

function sendMultipart(endpoint, file, channel = 'manual', extraFields = {}) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('channel', channel);
  Object.entries(extraFields).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      formData.append(key, value);
    }
  });
  return api.post(endpoint, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}

export async function analyzeImageUpload(file, channel = 'manual') {
  const { data } = await sendMultipart('/analyze-imagen', file, channel);
  return normalizeAnalysesPayload(data);
}

export async function analyzeVideoUpload(file, channel = 'manual') {
  const { data } = await sendMultipart('/analyze-video', file, channel);
  return normalizeAnalysesPayload(data);
}

export async function analyzeWebcamUpload(file, channel = 'webcam') {
  const { data } = await sendMultipart('/analyze-webcam', file, channel);
  return normalizeAnalysesPayload(data);
}

export async function analyzeWebcamFrame(file, channel = 'webcam-live', sessionId) {
  const extraFields = sessionId ? { session_id: sessionId } : {};
  const { data } = await sendMultipart('/analyze-webcam-frame', file, channel, extraFields);
  return data;
}

export async function startLiveSession(channel = 'webcam-live') {
  const { data } = await api.post('/media/live-session/start', { channel });
  return data;
}

export async function stopLiveSession(sessionId) {
  const { data } = await api.post('/media/live-session/stop', { session_id: sessionId });
  return normalizeAnalysesPayload(data);
}

export async function fetchModelMetadata() {
  const { data } = await api.get('/media/model-metadata');
  return data;
}

export async function fetchMediaHistory({ limit = 12, mediaType, sourceType, emotion } = {}) {
  const params = { limit };
  if (mediaType && mediaType !== 'all') {
    params.media_type = mediaType;
  }
  if (sourceType && sourceType !== 'all') {
    params.source_type = sourceType;
  }
  if (emotion && emotion !== 'all') {
    params.emotion = emotion;
  }
  const { data } = await api.get('/media/records', { params });
  return data;
}

export async function fetchMediaSnapshot(pathOrUrl) {
  const endpoint = normalizeFileEndpoint(pathOrUrl);
  if (!endpoint) {
    return null;
  }
  const response = await api.get(endpoint, { responseType: 'blob' });
  return response.data;
}
