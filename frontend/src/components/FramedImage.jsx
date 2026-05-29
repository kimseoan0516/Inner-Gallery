import framePng from '../assets/frame.png'

export default function FramedImage({ src, alt }) {
  return (
    <div style={{
      position: 'relative',
      width: 'calc(100% + 48px)',
      margin: '0 -24px',
      overflow: 'hidden',
    }}>
      <img
        src={framePng}
        alt=""
        style={{
          display: 'block',
          width: '100%',
          height: 'auto',
          transform: 'rotate(90deg)',
          pointerEvents: 'none',
        }}
      />
      {/* artwork fills the frame's transparent center — contain keeps full image */}
      <img
        src={src}
        alt={alt || '작품'}
        style={{
          position: 'absolute',
          top: '16%',
          left: '14%',
          width: '72%',
          height: '68%',
          objectFit: 'contain',
          zIndex: 1,
        }}
      />
    </div>
  )
}
