function ResultCard({ result }) {
  return (
    <div className="card" style={{ borderLeft: '6px solid #4f46e5' }}>
      <h3 style={{ marginTop: 0 }}>{result.sentiment_label?.toUpperCase()}</h3>
      <p style={{ color: '#4b5563' }}>{result.summary}</p>
      <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
        <div>
          <small>Polaridad</small>
          <div style={{ fontWeight: 700 }}>{result.polarity}</div>
        </div>
        <div>
          <small>Subjetividad</small>
          <div style={{ fontWeight: 700 }}>{result.subjectivity}</div>
        </div>
        <div>
          <small>Fecha</small>
          <div>{result.created_at ? new Date(result.created_at).toLocaleString() : 'N/D'}</div>
        </div>
      </div>
    </div>
  );
}

export default ResultCard;
