export default function EmotionBar({ label, score }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, height: 30 }}>
      <span style={{ width: 72, fontSize: 12, color: 'var(--body)', flexShrink: 0 }}>{label}</span>
      <div style={{
        flex: 1,
        height: 5,
        background: 'rgba(120,90,50,0.15)',
        borderRadius: 3,
        overflow: 'hidden',
      }}>
        <div style={{
          width: `${Math.round(score * 100)}%`,
          height: '100%',
          background: 'var(--gold3)',
          borderRadius: 3,
          transition: 'width 0.55s ease',
        }} />
      </div>
      <span style={{ width: 34, fontSize: 11, color: 'var(--sub)', textAlign: 'right', flexShrink: 0 }}>
        {Math.round(score * 100)}%
      </span>
    </div>
  )
}
