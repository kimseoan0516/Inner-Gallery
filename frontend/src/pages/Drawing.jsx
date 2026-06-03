import { useRef, useState, useEffect, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { saveJournal, sketchReflection } from '../api.js'
import { useAuth } from '../context/AuthContext.jsx'
import LoginModal from '../components/LoginModal.jsx'
import GoldDivider from '../components/GoldDivider.jsx'

const MODE_CONFIG = {
  free:  { label: '자유롭게',     question: '이 작품을 보고 마음에 남은 것을 자유롭게 남겨보세요.',  tool: 'pen',   size: 6  },
  color: { label: '색으로 채우기', question: '지금 감정에 가까운 색으로 화면을 채워보세요.',          tool: 'brush', size: 22 },
  line:  { label: '선으로 남기기', question: '이 작품을 보고 떠오른 선을 남겨보세요.',               tool: 'pen',   size: 2  },
  text:  { label: '문장 쓰기',     question: '작품이 건넨 말을 한 문장으로 적어보세요.',              tool: 'text',  size: 6  },
}

const BASE_COLORS = [
  '#FFFFFF', '#F4F0E8', '#E8D090', '#C9A84C',
  '#C85A3A', '#4A7C59', '#2C4A8C',
  '#7A5C8C', '#C8B4A0', '#8A8A8A', '#1A0800',
]

const SIZE_PRESETS = [
  { size: 2,  label: 'S' },
  { size: 8,  label: 'M' },
  { size: 22, label: 'L' },
]

const KEYWORDS = [
  '슬픔', '그리움', '평온', '설렘', '불안',
  '따뜻함', '공허함', '위로', '기쁨', '외로움', '감사', '해방감',
]

const MAX_HISTORY = 30

const Ic = ({ d, size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    {d}
  </svg>
)

export default function Drawing() {
  const nav      = useNavigate()
  const location = useLocation()
  const { user } = useAuth()
  const state    = location.state || {}
  const {
    thumbnail    = '',
    artworkImage = '',
    palette      = [],
    title        = '',
    artist       = '',
    moodColor    = '#F4F1EB',
    moods        = [],
  } = state

  const overlayImg = artworkImage || thumbnail

  const canvasRef     = useRef(null)
  const drawing       = useRef(false)
  const lastPt        = useRef(null)
  const historyRef    = useRef([])
  const historyIdxRef = useRef(-1)
  const textInputRef  = useRef(null)
  const bgImgRef      = useRef(null)

  const moodColorHex = moodColor || '#F4F1EB'
  const artworkAtmosphereColor = palette.length > 0
    ? (() => {
        const top = palette.slice(0, Math.min(3, palette.length))
        const avg = top.reduce((a, c) => [a[0]+c[0], a[1]+c[1], a[2]+c[2]], [0,0,0])
          .map(v => Math.max(0, Math.floor(v / top.length * 0.28)))
        return `rgb(${avg.join(',')})`
      })()
    : '#1C1008'

  const [sketchMode,     setSketchMode]     = useState('free')
  const [tool,           setTool]           = useState('pen')
  const [color,          setColor]          = useState('#C9A84C')
  const [size,           setSize]           = useState(6)
  const [bgMode,         setBgMode]         = useState('white')
  const [showSave,       setShowSave]       = useState(false)
  const [saveStep,       setSaveStep]       = useState('form')
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [savedOk,        setSavedOk]        = useState(false)
  const [savedSketchB64, setSavedSketchB64] = useState('')
  const [currentB64,     setCurrentB64]     = useState('')
  const [saving,         setSaving]         = useState(false)
  const [saveError,      setSaveError]      = useState('')
  const [saveTitle,      setSaveTitle]      = useState('')
  const [saveNote,       setSaveNote]       = useState('')
  const [saveKeywords,   setSaveKeywords]   = useState([])
  const [reflectionText, setReflectionText] = useState('')
  const [textPos,        setTextPos]        = useState(null)
  const [textVal,        setTextVal]        = useState('')
  const [customColor,      setCustomColor]      = useState('#C9A84C')
  const [eraserPos,        setEraserPos]        = useState(null)
  const [artworkPaletteIdx, setArtworkPaletteIdx] = useState(0)

  const paletteRgbColors = palette.map(c => Array.isArray(c) ? `rgb(${c[0]},${c[1]},${c[2]})` : String(c))
  const selectedArtworkColor = paletteRgbColors[artworkPaletteIdx] || artworkAtmosphereColor

  const canvasBg = bgMode === 'overlay' ? 'transparent'
    : bgMode === 'dark'    ? '#1C1008'
    : bgMode === 'mood'    ? moodColorHex
    : bgMode === 'artwork' ? selectedArtworkColor
    : '#F5F0E8'

  const effectiveBgColor = bgMode === 'overlay' ? '#1C1008'
    : bgMode === 'dark'    ? '#1C1008'
    : bgMode === 'mood'    ? moodColorHex
    : bgMode === 'artwork' ? selectedArtworkColor
    : '#F5F0E8'

  const bgModeName = { artwork: '작품 분위기', overlay: '원작 위에', white: '밝은 여백', dark: '어두운 배경', mood: '마음색' }[bgMode] || ''

  const bgModeOptions = [
    { key: 'white',   label: '밝게',    swatch: '#F5F0E8' },
    { key: 'dark',    label: '어둡게',  swatch: '#1C1008' },
    { key: 'artwork', label: '작품색',  swatch: artworkAtmosphereColor },
    ...(overlayImg ? [{ key: 'overlay', label: '원작 위', swatch: null }] : []),
    { key: 'mood',    label: '마음색',  swatch: moodColorHex },
  ]

  useEffect(() => {
    if (!overlayImg) return
    const img = new Image()
    img.onload = () => { bgImgRef.current = img }
    img.src = `data:image/jpeg;base64,${overlayImg}`
  }, [overlayImg])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const init = () => {
      const w = canvas.offsetWidth, h = canvas.offsetHeight
      if (!w || !h) { requestAnimationFrame(init); return }
      canvas.width = w; canvas.height = h
      const ctx = canvas.getContext('2d')
      historyRef.current = [ctx.getImageData(0, 0, w, h)]
      historyIdxRef.current = 0
    }
    requestAnimationFrame(init)
  }, [])

  const handleModeChange = useCallback((mode) => {
    setSketchMode(mode)
    const cfg = MODE_CONFIG[mode]
    setTool(cfg.tool); setSize(cfg.size)
  }, [])

  const saveSnap = useCallback(() => {
    const canvas = canvasRef.current; if (!canvas) return
    const ctx = canvas.getContext('2d')
    const snap = ctx.getImageData(0, 0, canvas.width, canvas.height)
    const next = historyRef.current.slice(0, historyIdxRef.current + 1)
    if (next.length >= MAX_HISTORY) next.shift()
    next.push(snap)
    historyRef.current = next; historyIdxRef.current = next.length - 1
  }, [])

  const undo = useCallback(() => {
    if (historyIdxRef.current <= 0) return
    historyIdxRef.current -= 1
    canvasRef.current.getContext('2d').putImageData(historyRef.current[historyIdxRef.current], 0, 0)
  }, [])

  const redo = useCallback(() => {
    if (historyIdxRef.current >= historyRef.current.length - 1) return
    historyIdxRef.current += 1
    canvasRef.current.getContext('2d').putImageData(historyRef.current[historyIdxRef.current], 0, 0)
  }, [])

  const getPos = (e, canvas) => {
    const rect = canvas.getBoundingClientRect()
    const src = e.touches ? e.touches[0] : e
    return {
      x: (src.clientX - rect.left) * (canvas.width / rect.width),
      y: (src.clientY - rect.top) * (canvas.height / rect.height),
    }
  }

  const startDraw = useCallback(e => {
    e.preventDefault()
    if (tool === 'text') {
      const canvas = canvasRef.current
      const rect = canvas.getBoundingClientRect()
      const src = e.touches ? e.touches[0] : e
      const rx = src.clientX - rect.left, ry = src.clientY - rect.top
      setTextPos({ x: rx, y: ry, cx: rx / rect.width * canvas.width, cy: ry / rect.height * canvas.height })
      setTextVal('')
      setTimeout(() => textInputRef.current?.focus(), 50)
      return
    }
    drawing.current = true; lastPt.current = getPos(e, canvasRef.current)
  }, [tool])

  const draw = useCallback(e => {
    e.preventDefault()
    if (!drawing.current || tool === 'text') return
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const pos = getPos(e, canvas)
    ctx.save()
    if (tool === 'eraser') { ctx.globalCompositeOperation = 'destination-out'; ctx.globalAlpha = 1 }
    else if (tool === 'brush') { ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 0.45 }
    else { ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1 }
    ctx.beginPath()
    ctx.moveTo(lastPt.current.x, lastPt.current.y)
    ctx.lineTo(pos.x, pos.y)
    ctx.strokeStyle = tool === 'eraser' ? 'rgba(0,0,0,1)' : color
    ctx.lineWidth = tool === 'eraser' ? size * 2.5 : size
    ctx.lineCap = 'round'; ctx.lineJoin = 'round'
    ctx.stroke(); ctx.restore()
    lastPt.current = pos
  }, [tool, color, size])

  const stopDraw = useCallback(() => {
    if (!drawing.current) return
    drawing.current = false; lastPt.current = null; saveSnap()
  }, [saveSnap])

  const commitText = useCallback(() => {
    if (!textPos || !textVal.trim()) { setTextPos(null); return }
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    ctx.save()
    ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1
    ctx.fillStyle = color
    ctx.font = `${size * 2 + 10}px 'Noto Serif KR', serif`
    ctx.fillText(textVal, textPos.cx, textPos.cy)
    ctx.restore()
    setTextPos(null); setTextVal(''); saveSnap()
  }, [textPos, textVal, color, size, saveSnap])

  const clear = () => {
    canvasRef.current.getContext('2d').clearRect(0, 0, canvasRef.current.width, canvasRef.current.height)
    saveSnap()
  }

  const fillWithColor = useCallback((fillColor) => {
    const canvas = canvasRef.current; if (!canvas) return
    const ctx = canvas.getContext('2d')
    ctx.save(); ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1
    ctx.fillStyle = fillColor; ctx.fillRect(0, 0, canvas.width, canvas.height)
    ctx.restore(); saveSnap()
  }, [saveSnap])

  const buildSketchB64 = () => {
    const canvas = canvasRef.current; if (!canvas) return ''
    const tc = document.createElement('canvas')
    tc.width = canvas.width; tc.height = canvas.height
    const ctx = tc.getContext('2d')
    if (bgMode === 'overlay' && bgImgRef.current) {
      ctx.fillStyle = '#1C1008'; ctx.fillRect(0, 0, tc.width, tc.height)
      ctx.globalAlpha = 0.45; ctx.drawImage(bgImgRef.current, 0, 0, tc.width, tc.height); ctx.globalAlpha = 1
    } else {
      ctx.fillStyle = effectiveBgColor; ctx.fillRect(0, 0, tc.width, tc.height)
    }
    ctx.drawImage(canvas, 0, 0)
    return tc.toDataURL('image/jpeg', 0.85).split(',')[1]
  }

  const advanceToReflection = () => {
    const b64 = buildSketchB64()
    setCurrentB64(b64); setSavedSketchB64(b64); setSaveStep('ask')
  }

  const askReflection = async (mode) => {
    setSaveStep('loading')
    try {
      const res = await sketchReflection({ sketchBase64: currentB64, palette, keywords: saveKeywords, guideQ: MODE_CONFIG[sketchMode].question, mode })
      setReflectionText(res.reflection || ''); setSaveStep('done')
    } catch { alert('회고를 가져오는 중 오류가 발생했습니다.'); setSaveStep('ask') }
  }

  const doSave = async (withReflection = true) => {
    if (!user) { setShowLoginModal(true); return }
    setSaving(true); setSaveError('')
    if (!withReflection) setReflectionText('')
    try {
      const now = new Date()
      const date = [now.getFullYear(), String(now.getMonth()+1).padStart(2,'0'), String(now.getDate()).padStart(2,'0')].join('-')
        + 'T' + [String(now.getHours()).padStart(2,'0'), String(now.getMinutes()).padStart(2,'0')].join(':')
      await saveJournal({
        date, entry_type: 'sketch',
        artwork_title: title, artwork_artist: artist,
        sketch_image: currentB64,
        sketch_title: saveTitle || '마음 스케치',
        sketch_note: saveNote,
        sketch_guide: MODE_CONFIG[sketchMode].question,
        moods: saveKeywords, mood_color: effectiveBgColor,
        mood_color_name: bgModeName,
        sketch_reflection: withReflection ? reflectionText : '',
      })
      setShowSave(false); setSavedOk(true)
    } catch { setSaveError('저장 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.') }
    finally { setSaving(false) }
  }

  const paletteColors = paletteRgbColors
  const toolCursor = tool === 'text' ? 'text' : tool === 'eraser' ? 'cell' : 'crosshair'

  // ── Saved screen ──────────────────────────────────────────────────────────
  if (savedOk) {
    const now = new Date()
    const dateStr = `${now.getFullYear()}년 ${String(now.getMonth()+1).padStart(2,'0')}월 ${String(now.getDate()).padStart(2,'0')}일`
    return (
      <div className="screen" style={{ background: 'var(--bg)' }}>
        <div className="nav-bar" style={{ background: 'var(--card)', borderBottom: '1px solid var(--line)' }}>
          <div style={{ flex: 1, textAlign: 'center' }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)', letterSpacing: 0.5 }}>마음 스케치</div>
            <div style={{ fontSize: 9, color: 'var(--gold)', fontStyle: 'italic', letterSpacing: 1.5 }}>Heart Sketch</div>
          </div>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '28px 20px 52px', display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ width: 52, height: 52, borderRadius: '50%', border: '1px solid rgba(184,145,42,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--gold2)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </div>
            <p style={{ fontSize: 17, fontWeight: 700, color: 'var(--text)', fontFamily: "'Noto Serif KR', serif", letterSpacing: 0.5, marginBottom: 6 }}>오늘의 마음 스케치가 저장되었어요</p>
            <p style={{ fontSize: 10, color: 'var(--sub)', letterSpacing: 1 }}>{dateStr}</p>
          </div>

          {(thumbnail || savedSketchB64) && (
            <div style={{ display: 'flex', gap: 10 }}>
              {thumbnail && (
                <div style={{ flex: 1, borderRadius: 8, overflow: 'hidden', border: '1px solid var(--line)' }}>
                  <img src={`data:image/jpeg;base64,${thumbnail}`} alt="" style={{ width: '100%', aspectRatio: '1', objectFit: 'cover', display: 'block' }} />
                  <p style={{ fontSize: 9, color: 'var(--sub)', textAlign: 'center', padding: '6px 0', letterSpacing: 1 }}>원작</p>
                </div>
              )}
              {savedSketchB64 && (
                <div style={{ flex: 1, borderRadius: 8, overflow: 'hidden', border: '1px solid rgba(184,145,42,0.3)' }}>
                  <img src={`data:image/jpeg;base64,${savedSketchB64}`} alt="" style={{ width: '100%', aspectRatio: '1', objectFit: 'cover', display: 'block' }} />
                  <p style={{ fontSize: 9, color: 'var(--gold)', textAlign: 'center', padding: '6px 0', letterSpacing: 1 }}>나의 스케치</p>
                </div>
              )}
            </div>
          )}

          <div className="card" style={{ padding: '20px 20px', display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div>
              <p style={{ fontSize: 16, fontWeight: 700, color: 'var(--text)', fontFamily: "'Noto Serif KR', serif", letterSpacing: 0.5, marginBottom: 3 }}>{saveTitle || '마음 스케치'}</p>
              {(title || artist) && <p style={{ fontSize: 10, color: 'var(--sub)' }}>{[title, artist].filter(Boolean).join(' · ')} 감상 후</p>}
            </div>
            <GoldDivider />
            {effectiveBgColor && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ width: 28, height: 28, borderRadius: 6, background: effectiveBgColor, border: '1px solid var(--line)', flexShrink: 0 }} />
                <div>
                  <p style={{ fontSize: 8, color: 'var(--gold)', letterSpacing: 2, marginBottom: 2 }}>오늘의 마음 배경</p>
                  <p style={{ fontSize: 12, color: 'var(--text)', fontWeight: 600 }}>{bgModeName}</p>
                </div>
              </div>
            )}
            {saveKeywords.length > 0 && (
              <div>
                <p style={{ fontSize: 8, color: 'var(--gold)', letterSpacing: 2, marginBottom: 8 }}>감정 키워드</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                  {saveKeywords.map(kw => (
                    <span key={kw} style={{ padding: '4px 12px', borderRadius: 20, fontSize: 11, background: 'rgba(184,145,42,0.08)', border: '1px solid rgba(184,145,42,0.25)', color: 'var(--gold2)' }}>{kw}</span>
                  ))}
                </div>
              </div>
            )}
            {saveNote && (
              <div style={{ borderLeft: '2px solid rgba(184,145,42,0.3)', paddingLeft: 14 }}>
                <p style={{ fontSize: 12, color: 'var(--body)', lineHeight: 1.8, fontStyle: 'italic', fontFamily: "'Noto Serif KR', serif" }}>"{saveNote}"</p>
              </div>
            )}
            {reflectionText && (
              <div style={{ borderTop: '1px solid var(--line)', paddingTop: 14 }}>
                <p style={{ fontSize: 8, color: 'var(--gold)', letterSpacing: 2, marginBottom: 8 }}>AI 스케치 회고</p>
                <p style={{ fontSize: 12, color: 'var(--body)', lineHeight: 1.9, fontFamily: "'Noto Serif KR', serif" }}>
                  {reflectionText.split('\n').filter(l => l.trim() && !l.startsWith('[')).join(' ')}
                </p>
              </div>
            )}
          </div>

          <p style={{ fontSize: 10, color: 'var(--sub)', textAlign: 'center', lineHeight: 1.8 }}>
            이 기록은 심리 진단이 아닌<br />자기 회고를 위한 감상 기록입니다.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <button className="btn-primary" style={{ height: 52 }} onClick={() => nav('/journal', { state: { refresh: Date.now() } })}>내 미술관에서 보기</button>
            <button className="btn-ghost" style={{ height: 44 }} onClick={() => {
              setSavedOk(false); setSavedSketchB64(''); setSaveTitle(''); setSaveNote(''); setSaveKeywords([]); setReflectionText('')
            }}>다시 그리기</button>
            <button onClick={() => nav('/')} style={{ background: 'transparent', border: 'none', color: 'var(--sub)', fontSize: 12, cursor: 'pointer', fontFamily: 'inherit', height: 36 }}>홈으로</button>
          </div>
        </div>
      </div>
    )
  }

  // ── Main drawing screen ───────────────────────────────────────────────────
  return (
    <div className="screen" style={{ display: 'flex', flexDirection: 'column', height: '100vh', maxHeight: '100vh', background: 'var(--bg)' }}>
      {showLoginModal && (
        <LoginModal onSuccess={() => { setShowLoginModal(false); doSave() }} onClose={() => setShowLoginModal(false)} />
      )}

      {/* Nav */}
      <div className="nav-bar" style={{ background: 'var(--card)', borderBottom: '1px solid var(--line)' }}>
        <button className="btn-ghost" onClick={() => nav(-1)} style={{ fontSize: 12 }}>← 돌아가기</button>
        <div style={{ flex: 1, textAlign: 'center' }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)', letterSpacing: 0.5 }}>마음 스케치</div>
          <div style={{ fontSize: 9, color: 'var(--gold)', fontStyle: 'italic', letterSpacing: 1.5 }}>Heart Sketch</div>
        </div>
        <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
          <button onClick={undo} title="실행 취소" style={{ background: 'transparent', border: 'none', color: 'var(--sub)', cursor: 'pointer', padding: '4px 6px', borderRadius: 4, display: 'flex', alignItems: 'center' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 14 4 9 9 4"/><path d="M20 20v-7a4 4 0 0 0-4-4H4"/></svg>
          </button>
          <button onClick={redo} title="다시 실행" style={{ background: 'transparent', border: 'none', color: 'var(--sub)', cursor: 'pointer', padding: '4px 6px', borderRadius: 4, display: 'flex', alignItems: 'center' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 14 20 9 15 4"/><path d="M4 20v-7a4 4 0 0 1 4-4h12"/></svg>
          </button>
        </div>
      </div>

      {/* Artwork info strip */}
      {(thumbnail || title) && (
        <div style={{ display: 'flex', gap: 10, padding: '8px 14px', background: 'var(--card)', borderBottom: '1px solid var(--line)', flexShrink: 0, alignItems: 'center' }}>
          {thumbnail && (
            <img src={`data:image/jpeg;base64,${thumbnail}`} alt="" style={{ width: 34, height: 26, objectFit: 'cover', borderRadius: 4, border: '1px solid var(--line)', flexShrink: 0 }} />
          )}
          <div style={{ minWidth: 0, flex: 1 }}>
            <p style={{ fontSize: 11, fontWeight: 700, color: 'var(--text)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{title || '명화'}</p>
            {artist && <p style={{ fontSize: 9, color: 'var(--sub)', letterSpacing: 0.5 }}>{artist}</p>}
          </div>
          {moods.length > 0 && (
            <div style={{ display: 'flex', gap: 4, flexShrink: 0 }}>
              {moods.slice(0, 2).map((m, i) => (
                <span key={i} style={{ fontSize: 9, color: 'var(--gold2)', background: 'rgba(184,145,42,0.08)', border: '1px solid rgba(184,145,42,0.2)', borderRadius: 10, padding: '2px 8px' }}>{m}</span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Mode selector */}
      <div style={{ padding: '10px 14px 0', background: 'var(--bg)', flexShrink: 0 }}>
        <div style={{ display: 'flex', gap: 6, justifyContent: 'center', marginBottom: 8 }}>
          {Object.entries(MODE_CONFIG).map(([key, cfg]) => (
            <button key={key} onClick={() => handleModeChange(key)} style={{
              padding: '6px 14px', borderRadius: 20, fontSize: 11, fontFamily: 'inherit', cursor: 'pointer',
              border: sketchMode === key ? '1px solid rgba(184,145,42,0.6)' : '1px solid var(--line)',
              background: sketchMode === key ? 'rgba(184,145,42,0.1)' : 'var(--card)',
              color: sketchMode === key ? 'var(--gold2)' : 'var(--sub)',
              fontWeight: sketchMode === key ? 700 : 400,
              transition: 'all 0.15s',
            }}>{cfg.label}</button>
          ))}
        </div>
        <p style={{ fontSize: 10, color: 'var(--sub)', textAlign: 'center', fontFamily: "'Noto Serif KR', serif", lineHeight: 1.6, paddingBottom: 8 }}>
          {MODE_CONFIG[sketchMode].question}
        </p>
      </div>

      {/* Canvas */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden', margin: '0 10px 8px', borderRadius: 10, border: '1px solid var(--line)', boxShadow: '0 4px 20px rgba(0,0,0,0.12)', minHeight: 0, background: canvasBg }}>
        {bgMode === 'overlay' && overlayImg && (
          <img src={`data:image/jpeg;base64,${overlayImg}`} alt="" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'contain', opacity: 0.45, pointerEvents: 'none', zIndex: 0 }} />
        )}
        <canvas
          ref={canvasRef}
          style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', display: 'block', touchAction: 'none', cursor: tool === 'eraser' ? 'none' : toolCursor, background: 'transparent', zIndex: 1 }}
          onMouseDown={startDraw}
          onMouseMove={e => {
            draw(e)
            if (tool === 'eraser') {
              const rect = e.currentTarget.getBoundingClientRect()
              setEraserPos({ x: e.clientX - rect.left, y: e.clientY - rect.top })
            }
          }}
          onMouseUp={stopDraw}
          onMouseLeave={e => { stopDraw(e); setEraserPos(null) }}
          onTouchStart={startDraw} onTouchMove={draw} onTouchEnd={stopDraw}
        />
        {tool === 'eraser' && eraserPos && (
          <div style={{ position: 'absolute', left: eraserPos.x - (size * 2.5) / 2, top: eraserPos.y - (size * 2.5) / 2, width: size * 2.5, height: size * 2.5, border: '1.5px solid rgba(0,0,0,0.5)', borderRadius: '50%', pointerEvents: 'none', zIndex: 5, boxShadow: '0 0 0 1px rgba(255,255,255,0.5)' }} />
        )}
        {textPos && (
          <div
            style={{ position: 'absolute', left: textPos.x, top: textPos.y - 24, zIndex: 10, cursor: 'move', userSelect: 'none' }}
            onMouseDown={e => {
              if (e.target === textInputRef.current) return
              const startX = e.clientX - textPos.x, startY = e.clientY - (textPos.y - 24)
              const onMove = mv => setTextPos(p => ({ ...p, x: mv.clientX - startX, y: mv.clientY - startY + 24 }))
              const onUp = () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp) }
              window.addEventListener('mousemove', onMove); window.addEventListener('mouseup', onUp)
            }}
          >
            <div style={{ fontSize: 9, color, opacity: 0.6, marginBottom: 2, letterSpacing: 1 }}>↕ 드래그로 이동</div>
            <input
              ref={textInputRef} value={textVal}
              onChange={e => setTextVal(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') commitText(); if (e.key === 'Escape') { setTextPos(null); setTextVal('') } }}
              onBlur={commitText}
              style={{ background: 'transparent', border: 'none', borderBottom: `1px solid ${color}`, color, fontSize: size * 2 + 10, fontFamily: "'Noto Serif KR', serif", outline: 'none', minWidth: 80, caretColor: color, cursor: 'text' }}
            />
          </div>
        )}
      </div>

      {/* Bottom controls */}
      <div style={{ padding: '6px 10px 12px', background: 'var(--card)', borderTop: '1px solid var(--line)', flexShrink: 0, overflowY: 'auto', maxHeight: '40vh' }}>

        {/* Row 1: tools + size + bg + clear + save */}
        <div style={{ display: 'flex', gap: 5, alignItems: 'center', marginBottom: 8 }}>
          {sketchMode !== 'color' && (
            <>
              {[
                { key: 'pen',    svg: <path d="M12 19l7-7 3 3-7 7-3-3z"/>, extra: <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/> },
                { key: 'brush',  svg: <><path d="M18.37 2.63 14 7l-1.59-1.59-2.83 2.83 1.59 1.59L7 14l-1.59-1.59-2.83 2.83L4 16.76a2.49 2.49 0 0 0 .18.24 2.1 2.1 0 0 0 2.88.3c.33-.31.7-.6 1.01-.88.25-.22.5-.45.77-.67l6.26 6.26 1.41-1.41-6.26-6.26.67-.77c.28-.31.57-.68.88-1.01a2.1 2.1 0 0 0 .3-2.88 2.49 2.49 0 0 0-.24-.18"/><path d="m21.37 5.37-2.83 2.83-2.83-2.83 2.83-2.83 2.83 2.83z"/></> },
                { key: 'eraser', svg: <><path d="m7 21-4.3-4.3c-1-1-1-2.5 0-3.4l9.6-9.6c1-1 2.5-1 3.4 0l5.6 5.6c1 1 1 2.5 0 3.4L13 21"/><path d="M22 21H7"/><path d="m5 11 9 9"/></> },
                { key: 'text',   svg: <><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></> },
              ].map(({ key, svg, extra }) => (
                <button key={key} onClick={() => { setTool(key); setEraserPos(null) }} style={{
                  width: 34, height: 34, borderRadius: 8, flexShrink: 0,
                  background: tool === key ? 'rgba(184,145,42,0.12)' : 'transparent',
                  border: tool === key ? '1px solid rgba(184,145,42,0.5)' : '1px solid transparent',
                  color: tool === key ? 'var(--gold2)' : 'var(--sub)',
                  cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{svg}{extra}</svg>
                </button>
              ))}
              <div style={{ width: 1, height: 20, background: 'var(--line)', flexShrink: 0 }} />
              {SIZE_PRESETS.map(({ size: s, label }) => (
                <button key={s} onClick={() => setSize(s)} style={{
                  width: 30, height: 30, borderRadius: 8, flexShrink: 0, fontSize: 10, fontFamily: 'inherit', fontWeight: 700,
                  background: size === s ? 'rgba(184,145,42,0.12)' : 'transparent',
                  border: size === s ? '1px solid rgba(184,145,42,0.5)' : '1px solid transparent',
                  color: size === s ? 'var(--gold2)' : 'var(--sub)',
                  cursor: 'pointer',
                }}>{label}</button>
              ))}
              <div style={{ width: 1, height: 20, background: 'var(--line)', flexShrink: 0 }} />
            </>
          )}

          {/* Background selector */}
          <span style={{ fontSize: 9, color: 'var(--sub)', fontWeight: 700, flexShrink: 0, letterSpacing: 0.5 }}>배경</span>
          <div className="hide-scroll" style={{ display: 'flex', gap: 4, alignItems: 'center', flex: 1, overflowX: 'auto' }}>
            {bgModeOptions.map(({ key, label, swatch }) => (
              <button key={key} onClick={() => setBgMode(key)} style={{
                display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0,
                padding: '4px 8px', borderRadius: 12, fontSize: 9, fontFamily: 'inherit', cursor: 'pointer',
                border: bgMode === key ? '1px solid rgba(184,145,42,0.6)' : '1px solid var(--line)',
                background: bgMode === key ? 'rgba(184,145,42,0.1)' : 'transparent',
                color: bgMode === key ? 'var(--gold2)' : 'var(--sub)',
                fontWeight: bgMode === key ? 700 : 400,
              }}>
                {swatch !== null
                  ? <div style={{ width: 10, height: 10, borderRadius: 2, background: swatch, border: '1px solid rgba(0,0,0,0.1)', flexShrink: 0 }} />
                  : <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2"/></svg>
                }
                {label}
              </button>
            ))}
            {/* 작품색 선택 시 팔레트 스와치 인라인 표시 */}
            {bgMode === 'artwork' && paletteRgbColors.length > 0 && (
              <>
                <div style={{ width: 1, height: 14, background: 'var(--line)', flexShrink: 0 }} />
                {paletteRgbColors.map((c, i) => (
                  <button key={i} onClick={() => setArtworkPaletteIdx(i)} style={{
                    width: 18, height: 18, borderRadius: 4, background: c, flexShrink: 0,
                    border: artworkPaletteIdx === i ? '2px solid var(--gold2)' : '1px solid var(--line)',
                    cursor: 'pointer', transform: artworkPaletteIdx === i ? 'scale(1.2)' : 'scale(1)', transition: 'transform 0.1s',
                  }} />
                ))}
              </>
            )}
          </div>

          <div style={{ width: 1, height: 20, background: 'var(--line)', flexShrink: 0 }} />
          <button onClick={clear} style={{ padding: '0 8px', height: 30, borderRadius: 8, fontSize: 10, fontFamily: 'inherit', background: 'transparent', border: '1px solid var(--line)', color: 'var(--sub)', cursor: 'pointer', flexShrink: 0, whiteSpace: 'nowrap' }}>초기화</button>
          <button onClick={() => { setShowSave(true); setSaveStep('form') }} style={{
            padding: '0 12px', height: 30, borderRadius: 8, fontSize: 11, fontFamily: 'inherit', flexShrink: 0,
            background: 'rgba(184,145,42,0.12)', border: '1px solid rgba(184,145,42,0.5)',
            color: 'var(--gold2)', cursor: 'pointer', fontWeight: 700, whiteSpace: 'nowrap',
          }}>저장</button>
        </div>

        {/* Color palette */}
        <div className="hide-scroll" style={{ display: 'flex', gap: 6, alignItems: 'center', overflowX: 'auto', paddingBottom: 2 }}>
          {BASE_COLORS.map((c, i) => (
            <button key={`b${i}`} onClick={() => { setColor(c); if (tool === 'eraser') setTool('pen'); if (sketchMode === 'color') fillWithColor(c) }} style={{
              width: 24, height: 24, borderRadius: 6, background: c, flexShrink: 0,
              border: color === c && tool !== 'eraser' ? '2px solid var(--gold2)' : '1px solid var(--line)',
              cursor: 'pointer', transform: color === c && tool !== 'eraser' ? 'scale(1.2)' : 'scale(1)', transition: 'transform 0.1s',
            }} />
          ))}
          <label style={{ position: 'relative', width: 24, height: 24, flexShrink: 0, cursor: 'pointer' }}>
            <div style={{ width: 24, height: 24, borderRadius: 6, background: 'conic-gradient(red, yellow, lime, aqua, blue, magenta, red)', border: '1px solid var(--line)' }} />
            <input type="color" value={customColor}
              onChange={e => { setCustomColor(e.target.value); setColor(e.target.value); if (tool === 'eraser') setTool('pen'); if (sketchMode === 'color') fillWithColor(e.target.value) }}
              style={{ position: 'absolute', inset: 0, opacity: 0, width: '100%', height: '100%', cursor: 'pointer' }}
            />
          </label>
          {paletteColors.length > 0 && (
            <>
              <div style={{ width: 1, height: 18, background: 'var(--line)', flexShrink: 0 }} />
              <span style={{ fontSize: 8, color: 'var(--sub)', flexShrink: 0, whiteSpace: 'nowrap' }}>원작</span>
              {paletteColors.map((c, i) => (
                <button key={`p${i}`} onClick={() => { setColor(c); if (tool === 'eraser') setTool('pen'); if (sketchMode === 'color') fillWithColor(c) }} style={{
                  width: 24, height: 24, borderRadius: 6, background: c, flexShrink: 0,
                  border: color === c && tool !== 'eraser' ? '2px solid var(--gold2)' : '1px solid var(--line)',
                  cursor: 'pointer', transform: color === c && tool !== 'eraser' ? 'scale(1.2)' : 'scale(1)', transition: 'transform 0.1s',
                }} />
              ))}
            </>
          )}
        </div>
      </div>

      {/* Save modal */}
      {showSave && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 200, background: 'rgba(0,0,0,0.5)', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
          <div style={{
            background: 'var(--card)', borderTop: '1px solid var(--line)',
            borderTopLeftRadius: 20, borderTopRightRadius: 20,
            padding: '20px 20px 44px',
            display: 'flex', flexDirection: 'column', gap: 16,
            maxHeight: '90vh', overflowY: 'auto',
          }}>
            <div style={{ width: 36, height: 4, borderRadius: 2, background: 'var(--line)', margin: '0 auto -4px' }} />

            {saveStep === 'form' && (<>
              <p style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)', fontFamily: "'Noto Serif KR', serif", textAlign: 'center' }}>이 스케치에 제목을 붙인다면?</p>
              <div>
                <div style={{ fontSize: 9, color: 'var(--gold)', letterSpacing: 2, fontWeight: 700, marginBottom: 6 }}>스케치 제목</div>
                <input value={saveTitle} onChange={e => setSaveTitle(e.target.value)} placeholder="예: 쉬어가도 되는 밤"
                  style={{ width: '100%', boxSizing: 'border-box', padding: '10px 14px', borderRadius: 10, background: 'var(--bg)', border: '1px solid var(--line)', color: 'var(--text)', fontSize: 13, fontFamily: 'inherit', outline: 'none' }} />
              </div>
              <div>
                <div style={{ fontSize: 9, color: 'var(--gold)', letterSpacing: 2, fontWeight: 700, marginBottom: 6 }}>오늘 마음에 한 문장</div>
                <textarea value={saveNote} onChange={e => setSaveNote(e.target.value)} placeholder="오늘 느낀 감정을 한 줄로 남겨보세요" rows={2}
                  style={{ width: '100%', boxSizing: 'border-box', padding: '10px 14px', borderRadius: 10, background: 'var(--bg)', border: '1px solid var(--line)', color: 'var(--text)', fontSize: 12, fontFamily: 'inherit', outline: 'none', resize: 'none', lineHeight: 1.7 }} />
              </div>
              <div>
                <div style={{ fontSize: 9, color: 'var(--gold)', letterSpacing: 2, fontWeight: 700, marginBottom: 8 }}>감정 키워드</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7 }}>
                  {KEYWORDS.map(kw => {
                    const on = saveKeywords.includes(kw)
                    return (
                      <button key={kw} onClick={() => setSaveKeywords(prev => on ? prev.filter(k => k !== kw) : [...prev, kw])} style={{
                        padding: '6px 14px', borderRadius: 20, fontSize: 12, fontFamily: 'inherit', cursor: 'pointer',
                        border: on ? '1px solid rgba(184,145,42,0.6)' : '1px solid var(--line)',
                        background: on ? 'rgba(184,145,42,0.1)' : 'transparent',
                        color: on ? 'var(--gold2)' : 'var(--sub)',
                        fontWeight: on ? 700 : 400,
                      }}>{kw}</button>
                    )
                  })}
                </div>
              </div>
              <button className="btn-primary" style={{ height: 52 }} onClick={advanceToReflection}>다음 →</button>
              <button onClick={() => { setShowSave(false); setSaveStep('form') }} style={{ background: 'transparent', border: 'none', color: 'var(--sub)', fontSize: 12, cursor: 'pointer', fontFamily: 'inherit', textAlign: 'center' }}>취소</button>
            </>)}

            {saveStep === 'ask' && (<>
              {currentB64 && (
                <div style={{ display: 'flex', justifyContent: 'center' }}>
                  <img src={`data:image/jpeg;base64,${currentB64}`} alt="" style={{ width: 120, height: 90, objectFit: 'cover', borderRadius: 10, border: '1px solid var(--line)' }} />
                </div>
              )}
              <div style={{ textAlign: 'center' }}>
                <p style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)', fontFamily: "'Noto Serif KR', serif", marginBottom: 6 }}>이 스케치를 AI가 함께 읽어볼까요?</p>
                <p style={{ fontSize: 10, color: 'var(--sub)', letterSpacing: 1 }}>AI Sketch Reflection</p>
              </div>
              <p style={{ fontSize: 12, color: 'var(--sub)', lineHeight: 1.8, textAlign: 'center' }}>
                AI는 당신의 감정을 판단하지 않아요.<br />사용된 색, 선, 여백을 바탕으로 스스로 돌아볼 수 있게 도와드려요.
              </p>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn-primary" style={{ flex: 1, height: 48 }} onClick={() => askReflection('short')}>짧게 회고 받기</button>
                <button className="btn-ghost" style={{ flex: 1, height: 48 }} onClick={() => askReflection('detail')}>자세히 회고 받기</button>
              </div>
              <button onClick={() => doSave(false)} disabled={saving} style={{ height: 44, borderRadius: 10, fontSize: 12, fontFamily: 'inherit', background: 'transparent', border: '1px solid var(--line)', color: 'var(--sub)', cursor: 'pointer' }}>
                {saving ? '저장 중…' : '회고 없이 저장하기'}
              </button>
              <button onClick={() => setSaveStep('form')} style={{ background: 'transparent', border: 'none', color: 'var(--sub)', fontSize: 11, cursor: 'pointer', fontFamily: 'inherit', textAlign: 'center' }}>← 뒤로</button>
            </>)}

            {saveStep === 'loading' && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 20, padding: '24px 0' }}>
                <div style={{ display: 'flex', gap: 10 }}>
                  {[0,1,2].map(i => <div key={i} style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--gold)', animation: `pulse 1.4s ${i * 0.46}s infinite` }} />)}
                </div>
                <p style={{ fontSize: 13, color: 'var(--sub)', lineHeight: 1.8, textAlign: 'center', fontFamily: "'Noto Serif KR', serif" }}>
                  스케치를 읽고 있어요…<br />
                  <span style={{ fontSize: 11 }}>색, 선, 여백을 살펴보는 중이에요</span>
                </p>
              </div>
            )}

            {saveStep === 'done' && (<>
              <p style={{ fontSize: 10, color: 'var(--gold)', letterSpacing: 2, fontWeight: 700, textAlign: 'center' }}>AI 스케치 회고</p>
              <div style={{ background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: 10, padding: '16px 18px' }}>
                {reflectionText.split('\n').map((line, i) => {
                  const isHeader = line.startsWith('[') && line.endsWith(']')
                  return line.trim() ? (
                    <p key={i} style={{ fontSize: isHeader ? 9 : 12, color: isHeader ? 'var(--gold)' : 'var(--body)', letterSpacing: isHeader ? 2 : 0.3, fontWeight: isHeader ? 700 : 400, lineHeight: 1.9, marginTop: isHeader ? 12 : 0, fontFamily: isHeader ? 'inherit' : "'Noto Serif KR', serif" }}>{line}</p>
                  ) : <div key={i} style={{ height: 6 }} />
                })}
              </div>
              <p style={{ fontSize: 10, color: 'var(--sub)', lineHeight: 1.7 }}>이 회고는 감정 진단이 아닌 감상 보조입니다. 마음에 남는 부분만 받아들이세요.</p>
              <button className="btn-primary" style={{ height: 52 }} onClick={() => doSave(true)} disabled={saving}>
                {saving ? '저장 중…' : '회고와 함께 저장하기'}
              </button>
              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={() => doSave(false)} disabled={saving} style={{ flex: 1, height: 42, borderRadius: 10, fontSize: 11, fontFamily: 'inherit', background: 'transparent', border: '1px solid var(--line)', color: 'var(--sub)', cursor: 'pointer' }}>회고 없이 저장</button>
                <button onClick={() => setSaveStep('ask')} style={{ flex: 1, height: 42, borderRadius: 10, fontSize: 11, fontFamily: 'inherit', background: 'transparent', border: '1px solid var(--line)', color: 'var(--sub)', cursor: 'pointer' }}>다시 회고 받기</button>
              </div>
            </>)}

            {saveError && <p style={{ fontSize: 11, color: '#D47070', textAlign: 'center', lineHeight: 1.6 }}>{saveError}</p>}
          </div>
        </div>
      )}
    </div>
  )
}
