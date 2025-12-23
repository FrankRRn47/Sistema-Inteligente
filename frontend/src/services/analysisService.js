import api from './api.js';

export async function analyzeText(text, channel = 'manual') {
  const { data } = await api.post('/analyze-text', { text, channel });
  return data;
}
