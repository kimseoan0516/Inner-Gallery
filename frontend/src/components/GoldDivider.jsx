export default function GoldDivider({ triple = false }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', height: 22, padding: '0 2px' }}>
      <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, transparent, rgba(140,106,38,0.22))' }} />
      {triple ? (
        <div style={{ display: 'flex', gap: 5, margin: '0 10px', alignItems: 'center' }}>
          {[0,1,2].map(i => (
            <div key={i} style={{
              width: i === 1 ? 7 : 5,
              height: i === 1 ? 7 : 5,
              background: `rgba(140,106,38,${i === 1 ? 0.65 : 0.38})`,
              transform: 'rotate(45deg)',
              flexShrink: 0,
            }} />
          ))}
        </div>
      ) : (
        <div style={{
          width: 6, height: 6,
          background: 'rgba(140,106,38,0.45)',
          transform: 'rotate(45deg)',
          margin: '0 10px',
          flexShrink: 0,
        }} />
      )}
      <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, rgba(140,106,38,0.22), transparent)' }} />
    </div>
  )
}
