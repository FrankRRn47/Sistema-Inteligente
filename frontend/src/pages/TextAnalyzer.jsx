import { useEffect, useState } from 'react';

import ResultCard from '../components/ResultCard.jsx';
import { analyzeText } from '../services/analysisService.js';

const HISTORY_KEY = 'ia_analysis_history';

function TextAnalyzer() {
  const [text, setText] = useState('');
  const [channel, setChannel] = useState('manual');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const stored = localStorage.getItem(HISTORY_KEY);
    if (stored) {
      setHistory(JSON.parse(stored));
    }
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!text.trim()) return;
    setLoading(true);
    setError('');
    try {
      const response = await analyzeText(text, channel);
      setResult(response.analysis);
      const updated = [response.analysis, ...history].slice(0, 10);
      setHistory(updated);
      localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
      setText('');
    } catch (err) {
      setError(err.response?.data?.message || 'No se pudo analizar el texto.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="app-container">
      <div className="card">
        <h1 className="page-title">Analizar texto</h1>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="form-group">
            {/* Selector de canal eliminado */}
          </div>
          <div className="form-group">
            <label htmlFor="text">Texto</label>
            <textarea id="text" rows="6" value={text} onChange={(e) => setText(e.target.value)} placeholder="Escribe o pega el texto a analizar" required />
          </div>
          {error && <p style={{ color: 'crimson' }}>{error}</p>}
          <button className="primary-btn" type="submit" disabled={loading}>
            {loading ? 'Analizando...' : 'Enviar'}
          </button>
        </form>
      </div>

      {result && (
        <div style={{ marginTop: '2rem' }}>
          <h2>Resultado reciente</h2>
          <ResultCard result={result} />
        </div>
      )}

      {history.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <h2>Historial local</h2>
          <div className="result-history">
            {history.map((item) => (
              <ResultCard key={item.id + item.created_at} result={item} />
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

export default TextAnalyzer;
