function StatCard({ label, value }) {
  return (
    <div className="card">
      <p style={{ margin: 0, color: '#6b7280' }}>{label}</p>
      <h2 style={{ margin: '0.5rem 0 0', fontSize: '2rem' }}>{value}</h2>
    </div>
  );
}

export default StatCard;
