export default function PaletteBar({ colors }) {
  if (!colors?.length) return null
  return (
    <div style={{ display: 'flex', gap: 6, height: 68 }}>
      {colors.map((c, i) => {
        const [r, g, b] = c.rgb
        return (
          <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
            <div style={{
              flex: 1,
              width: '100%',
              background: `rgb(${r},${g},${b})`,
              borderRadius: 8,
              border: '1px solid rgba(0,0,0,0.08)',
            }} />
            <span style={{ fontSize: 9, color: 'var(--sub)' }}>
              {Math.round((c.percentage ?? 0.2) * 100)}%
            </span>
          </div>
        )
      })}
    </div>
  )
}
