import { useCallback, useEffect, useMemo, useState } from 'react';

import MediaResultCard from '../components/MediaResultCard.jsx';
import StatCard from '../components/StatCard.jsx';
import { fetchMediaHistory, fetchModelMetadata } from '../services/mediaService.js';

const HERO_TITLE = 'Panel maestro de emociones';
const HERO_SUBTITLE = 'Explora cómo se comportan las emociones detectadas y filtra los registros según el sentimiento dominante.';
const ALL_EMOTIONS_LABEL = 'Todas las emociones';
const EMOTION_TRANSLATIONS = {
  angry: 'Enojo',
  disgust: 'Desagrado',
  fear: 'Miedo',
  happy: 'Felicidad',
  neutral: 'Neutral',
  sad: 'Tristeza',
  surprise: 'Sorpresa',
};

const getEmotionLabel = (label) => {
  if (!label) {
    return '';
  }
  const key = label.toString().trim().toLowerCase();
  return EMOTION_TRANSLATIONS[key] || label;
};



function Dashboard() {
  const [overviewPool, setOverviewPool] = useState([]);
  const [latestResults, setLatestResults] = useState([]);
  const [history, setHistory] = useState([]);
  const [activeEmotion, setActiveEmotion] = useState('all');
  const [availableEmotions, setAvailableEmotions] = useState([]);
  const [modelLabels, setModelLabels] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState('');

  const loadOverview = useCallback(async () => {
    try {
      const response = await fetchMediaHistory({ limit: 30 });
      const items = response.items || [];
      setOverviewPool(items);
      setLatestResults(items.slice(0, 4));
      setAvailableEmotions(response.filters?.available_emotions || []);
    } catch (loadError) {
      setError(loadError.response?.data?.message || 'No se pudo cargar el dashboard de emociones.');
    }
  }, []);

  const loadMetadata = useCallback(async () => {
    try {
      const metadata = await fetchModelMetadata();
      setModelLabels(metadata.labels || []);
    } catch (metadataError) {
      console.error('No se pudo obtener etiquetas del modelo', metadataError);
    }
  }, []);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    setError('');
    try {
      const response = await fetchMediaHistory({
        limit: 18,
        emotion: activeEmotion,
      });
      setHistory(response.items || []);
      setAvailableEmotions(response.filters?.available_emotions || []);
    } catch (loadError) {
      setError(loadError.response?.data?.message || 'No se pudo filtrar el historial.');
    } finally {
      setHistoryLoading(false);
    }
  }, [activeEmotion]);

  useEffect(() => {
    loadOverview();
    loadMetadata();
  }, [loadOverview, loadMetadata]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);



  const stats = useMemo(() => {
    const total = overviewPool.length;
    const emotionCounter = overviewPool.reduce((acc, item) => {
      if (!item.dominant_emotion) {
        return acc;
      }
      const key = item.dominant_emotion;
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});
    return {
      total,
      emotionCounter,
    };
  }, [overviewPool]);

  const filteredOverview = useMemo(() => {
    if (activeEmotion === 'all') {
      return overviewPool;
    }
    return overviewPool.filter((item) => {
      if (!item.dominant_emotion) return false;
      return item.dominant_emotion.toLowerCase() === activeEmotion.toLowerCase();
    });
  }, [overviewPool, activeEmotion]);

  const filteredLatestResults = useMemo(() => {
    if (activeEmotion === 'all') {
      return latestResults;
    }
    return latestResults.filter((item) => {
      if (!item.dominant_emotion) return false;
      return item.dominant_emotion.toLowerCase() === activeEmotion.toLowerCase();
    });
  }, [latestResults, activeEmotion]);

  const featuredLatestResults = filteredLatestResults.slice(0, 2);

  const filteredHistoryRecords = useMemo(() => {
    if (activeEmotion === 'all') {
      return history;
    }
    return history.filter((item) => {
      if (!item.dominant_emotion) return false;
      return item.dominant_emotion.toLowerCase() === activeEmotion.toLowerCase();
    });
  }, [history, activeEmotion]);

  const averageConfidence = filteredOverview.length
    ? filteredOverview.reduce((acc, item) => acc + (item.confidence || 0), 0) / filteredOverview.length
    : 0;

  const lastUpdated = filteredHistoryRecords[0]?.created_at || overviewPool[0]?.created_at;

  const emotionSnapshots = useMemo(() => {
    const snapshotMap = new Map();
    [...overviewPool, ...history].forEach((item) => {
      if (!item?.dominant_emotion || !item.snapshot_url) {
        return;
      }
      if (!snapshotMap.has(item.dominant_emotion)) {
        snapshotMap.set(item.dominant_emotion, item.snapshot_url);
      }
    });
    return snapshotMap;
  }, [overviewPool, history]);

  const activeEmotionLabel = activeEmotion === 'all' ? ALL_EMOTIONS_LABEL : getEmotionLabel(activeEmotion);
  const heroDescription = activeEmotion === 'all'
    ? HERO_SUBTITLE
    : `Mostrando capturas clasificadas como ${activeEmotionLabel}.`;
  const activeEmotionCount = activeEmotion === 'all'
    ? stats.total
    : stats.emotionCounter?.[activeEmotion] || 0;
  const activeEmotionCountLabel = activeEmotionCount > 0
    ? `${activeEmotionCount} ${activeEmotionCount === 1 ? 'captura' : 'capturas'}`
    : 'Sin capturas registradas';
  const historyBadgeLabel = historyLoading
    ? 'Actualizando…'
    : `${filteredHistoryRecords.length} ${filteredHistoryRecords.length === 1 ? 'registro' : 'registros'}${activeEmotion !== 'all' ? ` · ${activeEmotionLabel}` : ''}`;

  const handleEmotionSelect = useCallback((label) => {
    setActiveEmotion(label);
  }, []);

  const summaryCards = [
    { label: 'Muestras registradas', value: stats.total },
    { label: 'Promedio de confianza', value: `${(averageConfidence * 100).toFixed(1)}%` },
    { label: 'Emociones presentes', value: Object.keys(stats.emotionCounter || {}).length },
    { label: 'Última actualización', value: lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : 'N/D' },
  ];

  return (
    <section className="app-container emotion-dashboard">
      <div className="emotion-hero card">
        <div className="emotion-hero-head">
          <div>
            <p className="page-subtitle">Dashboard emociones</p>
            <h1>{HERO_TITLE}</h1>
            <p>{heroDescription}</p>
          </div>
          <div className="emotion-hero-meta">
            <span>{activeEmotionLabel}</span>
            <small>{activeEmotionCountLabel}</small>
          </div>
        </div>
        <div className="emotion-summary-grid">
          {summaryCards.map(({ label, value }) => (
            <StatCard key={label} label={label} value={value} />
          ))}
        </div>
        <div className="emotion-cascade-buttons">
          <button
            type="button"
            className={`emotion-preview-card all${activeEmotion === 'all' ? ' is-active' : ''}`}
            onClick={() => handleEmotionSelect('all')}
          >
            Todas
          </button>
          {Object.entries(EMOTION_TRANSLATIONS).map(([en, es]) => (
            <button
              key={en}
              type="button"
              className={`emotion-preview-card ${en}${activeEmotion === en ? ' is-active' : ''}`}
              onClick={() => handleEmotionSelect(en)}
            >
              {es}
            </button>
          ))}
        </div>
      </div>

      <div className="emotion-panels-grid">
        <div className="emotion-panel card">
          <div className="emotion-panel-header">
            <div>
              <p className="emotion-panel-kicker">Pulso inmediato</p>
              <h2 className="emotion-section-title">Últimas capturas filtradas</h2>
            </div>
            <span className="emotion-chip chip-live">En vivo</span>
          </div>
          {filteredLatestResults.length === 0 ? (
            <p className="emotion-dashboard-empty">
              {activeEmotion === 'all'
                ? 'Aún no hay registros recientes.'
                : `No hay registros recientes para ${activeEmotionLabel}.`}
            </p>
          ) : (
            <div className="emotion-latest-grid">
              {featuredLatestResults.map((item) => (
                <MediaResultCard key={`latest-${item.id}`} item={item} />
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="emotion-panel card">
        <div className="emotion-panel-header">
          <div>
            <p className="emotion-panel-kicker">Historial almacenado</p>
            <h2 className="emotion-section-title">Analíticas filtradas</h2>
          </div>
          <span className="emotion-chip">{historyBadgeLabel}</span>
        </div>
        {error && <p className="media-error">{error}</p>}
        {historyLoading ? (
          <p className="emotion-dashboard-empty">Cargando historial...</p>
        ) : filteredHistoryRecords.length === 0 ? (
          <p className="emotion-dashboard-empty">
            {activeEmotion === 'all'
              ? 'No hay registros almacenados aún.'
              : `No hay coincidencias para ${activeEmotionLabel} en el historial.`}
          </p>
        ) : (
          <div className="emotion-history-grid">
            {filteredHistoryRecords.map((item) => (
              <MediaResultCard key={`history-${item.id}`} item={item} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

export default Dashboard;
