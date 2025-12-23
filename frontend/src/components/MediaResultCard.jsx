import { API_BASE_URL } from '../services/api.js';
import useSnapshotPreview from '../hooks/useSnapshotPreview.js';

function MediaResultCard({ item }) {
  const baseUrl = API_BASE_URL.replace(/\/$/, '');
  const buildUrl = (path) => {
    if (!path) return null;
    if (path.startsWith('http')) return path;
    return `${baseUrl}${path}`;
  };

  const snapshotHref = buildUrl(item.snapshot_url);
  const originalHref = buildUrl(item.original_url);
  const counts = item.emotion_counts?.length
    ? item.emotion_counts.map(({ emotion_label: label, count: qty }) => [label, qty])
    : Object.entries(item.detections?.counts || {});
  const { previewUrl, fallbackUrl, state: previewState } = useSnapshotPreview(item.snapshot_url);
  const previewLink = previewUrl || fallbackUrl;
  const showPreview = Boolean(item.snapshot_url) && (previewState === 'loading' || previewState === 'ready');

  return (
    <div className="card media-result-card">
      <header className="media-result-header">
        <div>
          <p className="media-pill">{item.media_type?.toUpperCase()} · {item.source_type}</p>
          <h3>{item.dominant_emotion}</h3>
          <p className="media-confidence">Confianza {(item.confidence * 100).toFixed(2)}%</p>
        </div>
        <div className="media-links">
          {previewLink && (
            <a href={previewLink} target="_blank" rel="noreferrer">
              Ver captura
            </a>
          )}
          {originalHref && (
            <a href={originalHref} target="_blank" rel="noreferrer">
              Archivo original
            </a>
          )}
        </div>
      </header>
      {showPreview && (
        <figure className={`media-result-preview ${previewState === 'loading' ? 'is-loading' : ''}`}>
          {previewState === 'ready' && previewUrl ? (
            <img src={previewUrl} alt={`Captura del rostro clasificado como ${item.dominant_emotion}`} loading="lazy" />
          ) : (
            <div className="media-preview-skeleton">Renderizando captura…</div>
          )}
        </figure>
      )}
      {counts.length > 0 && (
        <ul className="media-counts">
          {counts.map(([label, qty]) => (
            <li key={label}>
              <span>{label}</span>
              <strong>{qty}</strong>
            </li>
          ))}
        </ul>
      )}
      <footer className="media-result-footer">
        <span>{item.created_at ? new Date(item.created_at).toLocaleString() : 'N/D'}</span>
        <span>Canal: {item.channel}</span>
      </footer>
    </div>
  );
}

export default MediaResultCard;
