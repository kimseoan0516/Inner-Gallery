import { useState, useRef, useEffect } from 'react'
import { searchByTitle, searchByArtist, findCandidates, isExactMatch, findBestMatch } from '../utils/fuzzyMatch.js'
import { ARTWORK_DB } from '../data/artworks.js'
import { cropToArtwork } from '../utils/detectArtwork.js'
import { useNavigate, useLocation } from 'react-router-dom'
import { useApp } from '../context/AppContext.jsx'
import { analyzeImage, quickMatch, quickQuality } from '../api.js'

const EMOTION_CATEGORIES = [
  { label: '가라앉음',         emotions: ['슬픔', '우울감', '외로움', '그리움', '공허함', '결핍', '상처', '자괴감', '절망', '무기력', '지침', '부담감'] },
  { label: '불안과 흔들림',     emotions: ['불안', '긴장감', '두려움', '막연함', '내적 갈등'] },
  { label: '분노와 복잡한 감정', emotions: ['짜증', '화', '증오', '애증'] },
  { label: '안정과 위로',       emotions: ['평온함', '편안함', '여유', '휴식', '온기', '위로', '수용', '화해', '환기'] },
  { label: '회복과 긍정',       emotions: ['회복', '긍정감', '희망', '기쁨', '설렘', '기대', '자신감', '열정', '생기', '자유로움', '풍족함', '영감'] },
  { label: '깊은 감각과 바라봄', emotions: ['감동', '경이로움', '황홀감', '성찰', '집중', '깨달음', '배려심', '호기심', '통찰'] },
]
const DEFAULT_EMOTIONS = ['슬픔', '외로움', '지침', '불안', '긴장감', '짜증', '평온함', '온기', '희망', '기쁨', '설렘', '감동', '경이로움']

function VintageFrame({ children, style }) {
  return (
    <div style={{
      position: 'relative',
      width: '100%',
      aspectRatio: '4 / 3',
      background: 'linear-gradient(135deg, #3d2b1f 0%, #1f140e 100%)',
      padding: '12px',
      borderTop: '5px solid #281a11',
      borderBottom: '5px solid #110905',
      borderLeft: '5px solid #1c1109',
      borderRight: '5px solid #1c1109',
      borderRadius: '2px',
      boxShadow: '0 16px 32px rgba(0,0,0,0.4), inset 0 1px 1px rgba(255,255,255,0.06)', 
      ...style
    }}>
      <div style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        background: 'var(--bg)',
        border: '1.5px solid rgba(184, 145, 66, 0.4)',
        boxShadow: 'inset 0 8px 16px rgba(0,0,0,0.12), inset 0 2px 8px rgba(0,0,0,0.06)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}>
        {children}
      </div>
      
      <div style={{ position: 'absolute', top: 20, left: 24, width: 8, height: 8, borderTop: '1px solid rgba(184, 145, 66, 0.3)', borderLeft: '1px solid rgba(184, 145, 66, 0.3)' }} />
      <div style={{ position: 'absolute', top: 20, right: 24, width: 8, height: 8, borderTop: '1px solid rgba(184, 145, 66, 0.3)', borderRight: '1px solid rgba(184, 145, 66, 0.3)' }} />
      <div style={{ position: 'absolute', bottom: 20, left: 24, width: 8, height: 8, borderBottom: '1px solid rgba(184, 145, 66, 0.3)', borderLeft: '1px solid rgba(184, 145, 66, 0.3)' }} />
      <div style={{ position: 'absolute', bottom: 20, right: 24, width: 8, height: 8, borderBottom: '1px solid rgba(184, 145, 66, 0.3)', borderRight: '1px solid rgba(184, 145, 66, 0.3)' }} />
    </div>
  )
}

function LoadingOverlay({ msg }) {
  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 100,
      background: 'radial-gradient(ellipse 100% 45% at 50% 0%, rgba(195,155,85,0.14) 0%, transparent 60%), var(--bg)',
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 28,
    }}>
      <div style={{ width: 72, height: 72, borderRadius: '50%', border: '1px solid rgba(201,168,76,0.22)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ width: 52, height: 52, borderRadius: '50%', border: '1px solid rgba(154,120,80,0.55)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ width: 10, height: 10, background: 'rgba(201,168,76,0.75)', transform: 'rotate(45deg)' }} />
        </div>
      </div>
      <p style={{ fontFamily: "'Noto Serif KR', serif", fontSize: 14, color: 'var(--body)', textAlign: 'center', lineHeight: 2, letterSpacing: 0.5 }}>{msg}</p>
      <div style={{ display: 'flex', gap: 10 }}>
        {[0, 1, 2].map(i => <div key={i} style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--gold3)', animation: `pulse 1.4s ${i * 0.46}s infinite` }} />)}
      </div>
    </div>
  )
}

function CameraView({ videoRef, cameraStream, flashActive, scanPhase, scanMatch, onStart, onCapture, onCancel, error, isMobile }) {
  const locked = scanPhase === 'locked'
  const scanning = scanPhase === 'scanning'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <VintageFrame>
        <div style={{ position: 'relative', width: '100%', height: '100%' }}>
          <video ref={videoRef} autoPlay playsInline muted
            style={{ width: '100%', height: '100%', objectFit: 'cover', display: cameraStream ? 'block' : 'none', transform: isMobile ? 'none' : 'scaleX(-1)' }} />

          {/* ── 스캔/인식 오버레이 ─────────────────── */}
          {cameraStream && (scanning || locked) && (
            <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
              {/* 인식 사각형 테두리 */}
              <div style={{
                position: 'absolute',
                top: '7%', left: '5%', right: '5%', bottom: '7%',
                border: locked ? '2px solid var(--gold3)' : '1.5px solid var(--sub)',
                boxShadow: locked ? '0 0 18px rgba(154,120,80,0.55), inset 0 0 18px rgba(201,168,76,0.08)' : 'none',
                animation: scanning ? 'scanPulse 2s ease-in-out infinite' : 'none',
                transition: 'border 0.25s, box-shadow 0.25s',
              }} />
              {/* 코너 마커 */}
              {[['top','left'],['top','right'],['bottom','left'],['bottom','right']].map(([v,h]) => (
                <div key={`${v}-${h}`} style={{
                  position: 'absolute',
                  [v]: '7%', [h]: '5%', width: 18, height: 18,
                  borderTop:    v==='top'    ? `2.5px solid ${locked ? 'var(--gold3)' : 'var(--body)'}` : 'none',
                  borderBottom: v==='bottom' ? `2.5px solid ${locked ? 'var(--gold3)' : 'var(--body)'}` : 'none',
                  borderLeft:   h==='left'   ? `2.5px solid ${locked ? 'var(--gold3)' : 'var(--body)'}` : 'none',
                  borderRight:  h==='right'  ? `2.5px solid ${locked ? 'var(--gold3)' : 'var(--body)'}` : 'none',
                  transition: 'border-color 0.25s',
                }} />
              ))}
              {/* 스캔 라인 (인식 중일 때만) */}
              {scanning && (
                <div style={{
                  position: 'absolute', left: '5%', right: '5%', height: 1,
                  background: 'linear-gradient(90deg, transparent, var(--sub), transparent)',
                  animation: 'scanLine 2s linear infinite',
                }} />
              )}
              {/* 하단 상태 텍스트 */}
              <div style={{
                position: 'absolute', bottom: '10%', left: 0, right: 0,
                display: 'flex', justifyContent: 'center',
              }}>
                {scanning && (
                  <span style={{ fontSize: 9, color: 'var(--sub)', letterSpacing: 1.5, fontFamily: "'Noto Serif KR', serif" }}>
                    작품을 스캔하는 중…
                  </span>
                )}
                {locked && scanMatch && (
                  <div style={{
                    background: 'rgba(28,20,12,0.82)', padding: '5px 14px', borderRadius: 3,
                    border: '1px solid rgba(154,120,80,0.45)',
                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2,
                  }}>
                    <span style={{ fontSize: 8, color: 'var(--gold3)', fontWeight: 700, letterSpacing: 2 }}>작품 인식됨</span>
                    <span style={{ fontSize: 11, color: 'var(--body)', fontFamily: "'Noto Serif KR', serif" }}>
                      {scanMatch.titleKo || scanMatch.title || scanMatch.artistKo || scanMatch.artist}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 캡처 플래시 */}
          {flashActive && (
            <div style={{ position: 'absolute', inset: 0, background: 'white', animation: 'flash 0.35s ease-out forwards', pointerEvents: 'none' }} />
          )}

          {/* 카메라 미시작 상태 */}
          {!cameraStream && (
            <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
              <div style={{ fontSize: 28, color: 'rgba(122,92,56,0.35)', fontFamily: 'serif', letterSpacing: 4 }}>◉</div>
              <p style={{ fontSize: 11, color: 'rgba(154,120,80,0.45)', letterSpacing: 1.5, textAlign: 'center' }}>카메라를 불러오는 중…</p>
              {error && <p style={{ fontSize: 10, color: '#D47070', textAlign: 'center', padding: '0 10px', lineHeight: 1.6 }}>{error}</p>}
            </div>
          )}
        </div>
      </VintageFrame>

      <div style={{ display: 'flex', gap: 12, marginTop: 12, alignItems: 'center' }}>
        {!cameraStream
          ? <button className="btn-primary" style={{ flex: 1 }} onClick={onStart}>카메라 시작</button>
          : <>
              <button className="btn-primary" style={{ flex: 2, fontSize: 13, letterSpacing: 0.5 }} onClick={onCapture}>
                {scanning ? '수동 촬영' : '촬영'}
              </button>
              <button className="btn-ghost" style={{ flex: 1 }} onClick={onCancel}>취소</button>
            </>
        }
      </div>
    </div>
  )
}

const STYLE_MAP = { healing: '아트 테라피', docent: '도슨트 해설', analysis: '시각 분석', short: '짧은 감상' }

export default function Upload({ mode: pageMode }) {
  const nav      = useNavigate()
  const location = useLocation()
  const { setResult, setPreEmotion } = useApp()

  const routineMode = location.state?.routineMode
  const routineHint = location.state?.routineHint

  const [selectedMode,  setSelectedMode]  = useState(routineMode || 'healing')
  const [preview,       setPreview]       = useState(null)
  const [file,          setFile]          = useState(null)
  const [loading,       setLoading]       = useState(false)
  const [loadingMsg,    setLoadingMsg]    = useState('분석을 시작합니다…')
  const [error,         setError]         = useState('')
  const [cameraStream,  setCameraStream]  = useState(null)
  const [myEmotion,     setMyEmotion]     = useState([])
  const [hintTitle,     setHintTitle]     = useState('') // 화면 표시용 (한국어+영어)
  const [hintArtist,    setHintArtist]    = useState('') // 화면 표시용 (한국어+영어)
  const [rawTitle,      setRawTitle]      = useState('') // AI 전달용 (영어 원본)
  const [rawArtist,     setRawArtist]     = useState('') // AI 전달용 (영어 원본)
  const [artworkType,   setArtworkType]   = useState('자동')
  const [analysisFocus, setAnalysisFocus] = useState(['전체'])
  const [titleSugs,     setTitleSugs]     = useState([])
  const [artistSugs,    setArtistSugs]    = useState([])
  const [confirmCands,  setConfirmCands]  = useState([])
  const [showConfirm,   setShowConfirm]   = useState(false)
  const [quickCands,    setQuickCands]    = useState([])
  const [quickLoading,  setQuickLoading]  = useState(false)
  const [qualityWarnings, setQualityWarnings] = useState([])
  const [flashActive,   setFlashActive]   = useState(false)
  const [scanPhase,     setScanPhase]     = useState('idle')  // 'idle'|'scanning'|'locked'
  const [scanMatch,     setScanMatch]     = useState(null)
  const [cropInfo,      setCropInfo]      = useState(null)    // { cropped, originalFile }
  const [autoMatchFailed, setAutoMatchFailed] = useState(false)
  const [showAllEmotions, setShowAllEmotions] = useState(false)

  const toggleEmo = (e) => setMyEmotion(prev =>
    prev.includes(e) ? prev.filter(x => x !== e) : [...prev, e]
  )

  const toggleFocus = (f) => {
    if (f === '전체') {
      setAnalysisFocus(['전체'])
    } else {
      setAnalysisFocus(prev => {
        const rest = prev.filter(x => x !== '전체')
        if (rest.includes(f)) {
          const next = rest.filter(x => x !== f)
          return next.length === 0 ? ['전체'] : next
        }
        return [...rest, f]
      })
    }
  }

  const applyRecommended = () => {
    setArtworkType('자동')
    setAnalysisFocus(['전체'])
    setSelectedMode('healing')
    setMyEmotion([])
  }

  const fileRef   = useRef()
  const videoRef  = useRef()
  const streamRef   = useRef(null)
  const autoScanRef = useRef(null)
  const scanLockRef = useRef(false)

  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)

  // Expand artist-only FAISS candidates → famous artworks from local DB
  const expandCands = (candidates) => {
    const normName = s => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').trim()
    const artistMatch = (dbA, faissA) => {
      const a = normName(dbA), b = normName(faissA)
      return a === b || a.includes(b) || b.includes(a)
    }
    const out = []
    for (const c of candidates) {
      if (!c.title) {
        const works = ARTWORK_DB.filter(a => artistMatch(a.artist, c.artist)).slice(0, 4)
        if (works.length > 0) works.forEach(a => out.push({ ...a, confidence: c.confidence, reason: c.reason || '' }))
        else out.push(c)
      } else {
        out.push(c)
      }
    }
    return out
  }

  // setImg: optionally auto-crop artwork region, then quickMatch
  const setImg = async (f, opts = {}) => {
    if (!f) return
    setError('')
    setQuickCands([])
    setCropInfo(null)
    setAutoMatchFailed(false)
    setQualityWarnings([])

    let activeFile = f

    // Auto-crop artwork region from photo (skip if preCands already provided)
    if (!opts.preCands && !opts.skipCrop) {
      const result = await cropToArtwork(f)
      if (result.cropped) {
        activeFile = result.file
        setCropInfo({ cropped: true, originalFile: f })
      }
    }

    setFile(activeFile)
    setPreview(URL.createObjectURL(activeFile))

    // 화질 체크 — 분석 전에 즉시 실행
    quickQuality(activeFile).then(res => {
      if (res?.warnings?.length > 0) setQualityWarnings(res.warnings)
    }).catch(() => {})

    if (opts.preCands) {
      if (opts.preCands.length > 0) {
        setQuickCands(opts.preCands)
        setAutoMatchFailed(false)
      } else {
        setAutoMatchFailed(true)
      }
      return
    }
    setQuickLoading(true)
    setQualityWarnings([])
    try {
      const [resMatch, resQual] = await Promise.all([
        quickMatch(activeFile).catch(() => null),
        quickQuality(activeFile).catch(() => null)
      ])
      
      if (resQual && resQual.warnings) {
        setQualityWarnings(resQual.warnings)
      }

      const expanded = resMatch?.candidates?.length > 0 ? expandCands(resMatch.candidates).slice(0, 5) : []
      if (expanded.length > 0) {
        setQuickCands(expanded)
        setAutoMatchFailed(false)
      } else {
        setQuickCands([])
        setAutoMatchFailed(true)
      }
    } catch {
      setAutoMatchFailed(true)
    } finally {
      setQuickLoading(false)
    }
  }

  const stopAutoScan = () => {
    clearInterval(autoScanRef.current)
    autoScanRef.current = null
    scanLockRef.current = false
    setScanPhase('idle')
    setScanMatch(null)
  }

  const startCam = async () => {
    try {
      let stream
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } },
        })
      } catch {
        stream = await navigator.mediaDevices.getUserMedia({ video: true })
      }
      streamRef.current = stream
      setCameraStream(stream)
      if (videoRef.current) videoRef.current.srcObject = stream
      // Begin auto-scan after camera is ready
      setTimeout(() => startAutoScan(), 600)
    } catch {
      setError('카메라 접근 권한이 필요합니다. 브라우저 설정에서 카메라를 허용해주세요.')
    }
  }

  const stopCam = () => {
    stopAutoScan()
    streamRef.current?.getTracks().forEach(t => t.stop())
    streamRef.current = null
    setCameraStream(null)
  }

  const startAutoScan = () => {
    if (autoScanRef.current) return
    setScanPhase('scanning')
    autoScanRef.current = setInterval(async () => {
      if (scanLockRef.current) return
      const v = videoRef.current
      if (!v || v.readyState < 2 || v.videoWidth === 0) return
      scanLockRef.current = true
      try {
        const canvas = captureFramedCanvas(v)
        await new Promise(resolve => {
          canvas.toBlob(async (blob) => {
            if (!blob) { resolve(); return }
            const f = new File([blob], 'scan.jpg', { type: 'image/jpeg' })
            try {
              const res = await quickMatch(f)
              if (res?.candidates?.length > 0 && res.candidates[0].confidence >= 62) {
                clearInterval(autoScanRef.current)
                autoScanRef.current = null
                const expanded = expandCands(res.candidates)
                setScanPhase('locked')
                setScanMatch(expanded[0])
                // Brief pause so user sees the "locked" state, then auto-capture
                setTimeout(async () => {
                  setFlashActive(true)
                  setTimeout(() => setFlashActive(false), 400)
                  const cropResult = await cropToArtwork(f)
                  const activeFile = cropResult.cropped ? cropResult.file : f
                  if (cropResult.cropped) setCropInfo({ cropped: true, originalFile: f })
                  setFile(activeFile)
                  setPreview(URL.createObjectURL(activeFile))
                  setError('')
                  setQuickCands(expanded.slice(0, 5))
                  stopCam()
                }, 750)
              }
            } catch { /* non-fatal */ }
            resolve()
          }, 'image/jpeg', 0.85)
        })
      } finally {
        scanLockRef.current = false
      }
    }, 1800)
  }

  // Auto-start camera on mount; clean up on unmount
  useEffect(() => {
    if (pageMode === 'camera') startCam()
    return () => stopCam()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 액자 오버레이 영역(top:7% left:5% right:5% bottom:7%)만 잘라서 캔버스 반환
  const captureFramedCanvas = (v) => {
    const vw = v.videoWidth, vh = v.videoHeight
    const full = document.createElement('canvas')
    full.width = vw; full.height = vh
    const fCtx = full.getContext('2d')
    if (!isMobile) { fCtx.translate(vw, 0); fCtx.scale(-1, 1) }
    fCtx.drawImage(v, 0, 0)
    const x = Math.round(vw * 0.05), y = Math.round(vh * 0.07)
    const w = Math.round(vw * 0.90), h = Math.round(vh * 0.86)
    const crop = document.createElement('canvas')
    crop.width = w; crop.height = h
    crop.getContext('2d').drawImage(full, x, y, w, h, 0, 0, w, h)
    return crop
  }

  const capture = () => {
    const v = videoRef.current; if (!v) return
    stopAutoScan()
    setFlashActive(true)
    setTimeout(() => setFlashActive(false), 400)
    const c = captureFramedCanvas(v)
    c.toBlob(blob => { setImg(new File([blob], 'capture.jpg', { type: 'image/jpeg' })); stopCam() }, 'image/jpeg', 0.92)
  }

  const onTitleChange = (val) => {
    setHintTitle(val)
    setRawTitle(val)  // 직접 입력 시 그대로 사용
    setTitleSugs(val.length >= 2 ? searchByTitle(val) : [])
  }
  const onArtistChange = (val) => {
    setHintArtist(val)
    setRawArtist(val)  // 직접 입력 시 그대로 사용
    setArtistSugs(val.length >= 2 ? searchByArtist(val) : [])
  }
  const selectSuggestion = (artwork) => {
    // 화면 표시: 한국어+영어+연도
    const titleDisplay = artwork.titleKo
      ? `${artwork.titleKo} (${artwork.title}${artwork.year ? ', ' + artwork.year : ''})`
      : artwork.year ? `${artwork.title} (${artwork.year})` : artwork.title
    const artistDisplay = artwork.artistKo
      ? `${artwork.artistKo} (${artwork.artist})`
      : artwork.artist
    setHintTitle(titleDisplay)
    setHintArtist(artistDisplay)
    // AI 전달: 영어 원본만
    setRawTitle(artwork.title)
    setRawArtist(artwork.artist)
    setTitleSugs([])
    setArtistSugs([])
  }

  const doAnalyze = async (title, artist) => {
    setPreEmotion(myEmotion)
    setLoading(true); setError('')
    setLoadingMsg('작품을 감상하는 중입니다…')
    try {
      const match = (title || artist) ? findBestMatch(title, artist) : null
      const artworkDescription = (match?.description) || ''
      const data = await analyzeImage({
        file,
        mode: selectedMode,
        hintTitle: title,
        hintArtist: artist,
        userIdentityProvided: Boolean(title || artist),
        artworkType,
        analysisFocus: analysisFocus.join('·'),
        artworkDescription,
      })
      setResult(data)
      nav('/results')
    } catch (e) {
      setError(e.response?.data?.detail || e.message || '오류가 발생했습니다')
      setLoading(false)
    }
  }

  const handleAnalyzeClick = () => {
    if (!file) { setError('이미지를 선택해주세요'); return }
    const searchTitle  = rawTitle  || hintTitle
    const searchArtist = rawArtist || hintArtist
    if (searchTitle || searchArtist) {
      const cands = findCandidates(searchTitle, searchArtist)
      if (cands.length > 0 && !isExactMatch(searchTitle, searchArtist, cands[0])) {
        setConfirmCands(cands); setShowConfirm(true); return
      }
    }
    doAnalyze(searchTitle, searchArtist)
  }

  const settingsSummary = [
    artworkType === '자동' ? '자동 추천' : artworkType,
    analysisFocus.join(' · '),
    STYLE_MAP[selectedMode],
    myEmotion.length > 0 && myEmotion[0] !== '건너뜀'
      ? `감상 전: ${myEmotion.slice(0, 2).join('·')}${myEmotion.length > 2 ? '…' : ''}` : null,
  ].filter(Boolean).join('  ·  ')

  if (loading) return <LoadingOverlay msg={loadingMsg} />

  return (
    <div className="screen">
      <div className="nav-bar">
        <button className="btn-ghost" onClick={() => { stopCam(); nav('/') }}>← 돌아가기</button>
        <h2 style={{ flex: 1, textAlign: 'center', fontSize: 14, fontWeight: 600, color: 'var(--text)', letterSpacing: 1 }}>
          {pageMode === 'camera' ? '카메라 스캔' : '이미지 업로드'}
        </h2>
        <div style={{ width: 80 }} />
      </div>

      <div className="screen-scroll" style={{ padding: '20px 20px 44px', display: 'flex', flexDirection: 'column', gap: 16 }}>

        {routineHint && (
          <div style={{ background: 'rgba(122,92,56,0.09)', border: '1px solid rgba(122,92,56,0.28)', borderLeft: '3px solid rgba(154,120,80,0.40)', borderRadius: 4, padding: '10px 14px' }}>
            <p style={{ fontSize: 10, color: 'var(--gold2)', fontWeight: 700, letterSpacing: 1.5, marginBottom: 3 }}>감상 루틴 모드</p>
            <p style={{ fontSize: 11, color: 'var(--body)', lineHeight: 1.7 }}>{routineHint} 모드로 작품을 분석합니다.</p>
          </div>
        )}

        {/* Camera / Upload zone */}
        {pageMode === 'camera' && !preview ? (
          <CameraView
            videoRef={videoRef}
            cameraStream={cameraStream}
            flashActive={flashActive}
            scanPhase={scanPhase}
            scanMatch={scanMatch}
            onStart={startCam}
            onCapture={capture}
            onCancel={stopCam}
            error={error}
            isMobile={isMobile}
          />
        ) : (
          <>
            {preview ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <VintageFrame>
                  <img src={preview} alt="preview" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                </VintageFrame>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 2px' }}>
                  <span style={{ fontSize: 10, color: 'var(--sub)', flex: 1 }}>이미지가 준비되었습니다</span>
                  <button className="btn-ghost" style={{ fontSize: 11, padding: '5px 12px', height: 32 }}
                    onClick={() => {
                      setPreview(null); setFile(null)
                      setHintTitle(''); setHintArtist('')
                      setRawTitle(''); setRawArtist('')
                      setQuickCands([])
                      if (pageMode === 'camera') setTimeout(startCam, 50)
                      else stopAutoScan()
                    }}>
                    {pageMode === 'camera' ? '다시 촬영' : '다른 이미지 선택'}
                  </button>
                </div>
                {/* ── 화질 경고 (분석 전 즉시 표시) ──────────────── */}
                {qualityWarnings.length > 0 && (
                  <div style={{
                    background: 'rgba(154,100,60,0.10)',
                    border: '1px solid rgba(184,120,42,0.35)',
                    borderLeft: '3px solid rgba(184,120,42,0.6)',
                    borderRadius: 4,
                    padding: '10px 14px',
                  }}>
                    <p style={{ fontSize: 10, color: 'var(--gold2)', fontWeight: 700, letterSpacing: 1.5, marginBottom: 5 }}>
                      화질 안내
                    </p>
                    {qualityWarnings.map((w, i) => (
                      <p key={i} style={{ fontSize: 11, color: 'var(--sub)', lineHeight: 1.8 }}>· {w}</p>
                    ))}
                  </div>
                )}

                {/* ── 이미지 선택 즉시 Top-5 후보 ──────────────── */}
                {quickLoading && (
                  <div style={{
                    background: 'var(--card)', border: '1px solid var(--line)',
                    borderRadius: 4, padding: '12px 16px',
                    display: 'flex', alignItems: 'center', gap: 10, backdropFilter: 'blur(8px)'
                  }}>
                    <div style={{ display: 'flex', gap: 5 }}>
                      {[0,1,2].map(i => <div key={i} style={{ width: 5, height: 5, borderRadius: '50%', background: 'var(--gold3)', animation: `pulse 1.2s ${i * 0.4}s infinite` }} />)}
                    </div>
                    <span style={{ fontSize: 11, color: 'var(--sub)', letterSpacing: 0.5 }}>작품을 인식하는 중입니다…</span>
                  </div>
                )}

                {!quickLoading && quickCands.length > 0 && (
                  <div style={{ background: 'var(--card)', border: '1px solid var(--line)', borderRadius: 4, padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 10, backdropFilter: 'blur(8px)' }}>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                      <span style={{ fontSize: 9, color: 'var(--gold3)', fontWeight: 700, letterSpacing: 2 }}>◈  혹시 이 작품인가요?</span>
                      <span style={{ fontSize: 9, color: 'rgba(154,120,80,0.45)', letterSpacing: 1 }}>
                        {quickCands[0]?.confidence >= 75 ? '높은 확신도 · 선택하면 자동 입력' : 'AI 추정 · 참고용으로만 활용하세요'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {quickCands.map((c, i) => (
                        <button key={i}
                          onClick={() => {
                            const artistDisplay = c.artistKo ? `${c.artistKo} (${c.artist})` : c.artist
                            setHintArtist(artistDisplay)
                            setRawArtist(c.artist)
                            if (c.title) {
                              const titleDisplay = c.titleKo
                                ? `${c.titleKo} (${c.title}${c.year ? ', ' + c.year : ''})`
                                : c.year ? `${c.title} (${c.year})` : c.title
                              setHintTitle(titleDisplay)
                              setRawTitle(c.title)
                            }
                            setQuickCands([])
                          }}
                          style={{
                            display: 'flex', alignItems: 'center', gap: 12,
                            background: i === 0 ? 'rgba(154,120,80,0.06)' : 'rgba(255,255,255,0.01)',
                            border: i === 0 ? '1px solid rgba(154,120,80,0.30)' : '1px solid rgba(154,120,80,0.12)',
                            borderRadius: 4, padding: '10px 12px',
                            cursor: 'pointer', fontFamily: 'inherit',
                            textAlign: 'left', transition: 'all 0.15s',
                          }}
                          onMouseEnter={e => {
                            e.currentTarget.style.background = 'rgba(154,120,80,0.10)'
                            e.currentTarget.style.borderColor = 'rgba(176,144,96,0.35)'
                          }}
                          onMouseLeave={e => {
                            e.currentTarget.style.background = i === 0 ? 'rgba(154,120,80,0.06)' : 'rgba(255,255,255,0.01)'
                            e.currentTarget.style.borderColor = i === 0 ? 'rgba(154,120,80,0.30)' : 'rgba(154,120,80,0.12)'
                          }}
                        >
                          <div style={{ width: 28, flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3 }}>
                            <span style={{ fontSize: 8, color: i === 0 ? 'var(--gold3)' : 'rgba(154,120,80,0.45)', fontWeight: 700 }}>#{i + 1}</span>
                            <div style={{ width: 3, height: 28, background: 'rgba(154,120,80,0.2)', borderRadius: 2, overflow: 'hidden' }}>
                              <div style={{ width: '100%', height: `${c.confidence}%`, background: i === 0 ? 'var(--gold3)' : 'rgba(154,120,80,0.35)', borderRadius: 2 }} />
                            </div>
                            <span style={{ fontSize: 7, color: 'var(--sub)' }}>{c.confidence}%</span>
                          </div>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            {c.title ? (
                              <>
                                <p style={{ fontSize: 12, color: 'var(--body)', fontWeight: i === 0 ? 700 : 400, marginBottom: 2, fontFamily: "'Noto Serif KR', serif", lineHeight: 1.4 }}>
                                  {c.titleKo || c.title}
                                  {c.titleKo && <span style={{ fontSize: 9, color: 'var(--sub)', marginLeft: 5, fontWeight: 400 }}>{c.title}</span>}
                                </p>
                                <p style={{ fontSize: 10, color: 'var(--sub)' }}>{c.artistKo || c.artist}{c.year ? ` · ${c.year}` : ''}</p>
                              </>
                            ) : (
                              <>
                                <p style={{ fontSize: 12, color: 'var(--body)', fontWeight: i === 0 ? 700 : 400, marginBottom: 2, fontFamily: "'Noto Serif KR', serif", lineHeight: 1.4 }}>
                                  {c.artistKo || c.artist}
                                  {c.artistKo && <span style={{ fontSize: 9, color: 'var(--sub)', marginLeft: 5, fontWeight: 400 }}>{c.artist}</span>}
                                </p>
                                <p style={{ fontSize: 10, color: 'var(--sub)' }}>
                                  {c.genre || ''}
                                  {c.year ? ` · ${c.year}` : ''}
                                  <span style={{ marginLeft: 6, color: 'rgba(122,92,56,0.55)', fontStyle: 'italic' }}>작품명 직접 입력</span>
                                </p>
                              </>
                            )}
                            {c.reason && <p style={{ fontSize: 9, color: 'rgba(154,120,80,0.65)', marginTop: 3, lineHeight: 1.4, fontStyle: 'italic' }}>{c.reason}</p>}
                          </div>
                          <span style={{ fontSize: 10, color: 'rgba(154,120,80,0.40)', flexShrink: 0 }}>›</span>
                        </button>
                      ))}
                    </div>
                    <button onClick={() => setQuickCands([])} style={{ background: 'transparent', border: 'none', fontSize: 9, color: 'rgba(122,92,56,0.50)', cursor: 'pointer', fontFamily: 'inherit', letterSpacing: 0.5, textAlign: 'left', padding: 0 }}>
                      해당 없음 — 직접 입력하기
                    </button>
                  </div>
                )}

                {!quickLoading && autoMatchFailed && file && (
                  <p style={{ fontSize: 9, color: 'rgba(122,92,56,0.50)', textAlign: 'center', letterSpacing: 0.5 }}>
                    작품을 자동 인식하지 못했어요. 아래에 직접 입력해주세요.
                  </p>
                )}

                <div style={{ background: 'var(--card)', border: '1px solid var(--line)', borderRadius: 4, padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 10, backdropFilter: 'blur(8px)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                    <div style={{ fontFamily: "'Noto Serif KR', serif", fontSize: 11.5, fontWeight: 700, color: 'var(--gold3)', letterSpacing: 1 }}>작품 정보 입력</div>
                    <div style={{ fontSize: 9, color: 'rgba(154,120,80,0.50)', letterSpacing: 0.5 }}>선택 사항</div>
                  </div>
                  <p style={{ fontSize: 9.5, color: 'rgba(154, 120, 80, 0.45)', lineHeight: 1.5, letterSpacing: 0.2 }}>
                    작품 정보를 모르거나 정확하지 않아도 괜찮아요. 이미지만으로도 색채와 구도를 깊이 있게 분석해 드립니다.
                  </p>

                  <div style={{ position: 'relative' }}>
                    <input value={hintTitle} onChange={e => onTitleChange(e.target.value)} onBlur={() => setTimeout(() => setTitleSugs([]), 180)}
                      placeholder="작품명 (별이 빛나는 밤, 모나리자…)"
                      style={{ width: '100%', boxSizing: 'border-box', padding: '9px 12px', borderRadius: titleSugs.length > 0 ? '3px 3px 0 0' : 3, background: 'var(--bg)', border: '1px solid var(--line)', color: 'var(--text)', fontSize: 13, fontFamily: 'inherit', outline: 'none' }} />
                    {titleSugs.length > 0 && (
                      <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 30, background: 'var(--bg2)', border: '1px solid rgba(154,120,80,0.3)', borderTop: 'none', borderRadius: '0 0 3px 3px', overflow: 'hidden' }}>
                        {titleSugs.map(a => (
                          <button key={a.id} onMouseDown={e => { e.preventDefault(); selectSuggestion(a) }}
                            style={{ display: 'block', width: '100%', textAlign: 'left', padding: '8px 12px', background: 'transparent', border: 'none', borderBottom: '1px solid rgba(154,120,80,0.15)', cursor: 'pointer', fontFamily: 'inherit' }}>
                            <span style={{ fontSize: 12, color: 'var(--body)' }}>{a.titleKo || a.title}</span>
                            {a.titleKo && <span style={{ fontSize: 10, color: 'var(--sub)', marginLeft: 6 }}>({a.title})</span>}
                            <span style={{ fontSize: 10, color: 'rgba(154,120,80,0.5)', marginLeft: 6 }}>— {a.artistKo || a.artist}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  <div style={{ position: 'relative' }}>
                    <input value={hintArtist} onChange={e => onArtistChange(e.target.value)} onBlur={() => setTimeout(() => setArtistSugs([]), 180)}
                      placeholder="화가명 (고흐, 모네, 클림트…)"
                      style={{ width: '100%', boxSizing: 'border-box', padding: '9px 12px', borderRadius: artistSugs.length > 0 ? '3px 3px 0 0' : 3, background: 'var(--bg)', border: '1px solid var(--line)', color: 'var(--text)', fontSize: 13, fontFamily: 'inherit', outline: 'none' }} />
                    {artistSugs.length > 0 && (
                      <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 30, background: 'var(--bg2)', border: '1px solid rgba(154,120,80,0.3)', borderTop: 'none', borderRadius: '0 0 3px 3px', overflow: 'hidden' }}>
                        {artistSugs.map(a => (
                          <button key={`${a.id}-a`} onMouseDown={e => {
                              e.preventDefault()
                              const artistDisplay = a.artistKo ? `${a.artistKo} (${a.artist})` : a.artist
                              setHintArtist(artistDisplay)
                              setRawArtist(a.artist)
                              setArtistSugs([])
                            }}
                            style={{ display: 'block', width: '100%', textAlign: 'left', padding: '8px 12px', background: 'transparent', border: 'none', borderBottom: '1px solid rgba(154,120,80,0.15)', cursor: 'pointer', fontFamily: 'inherit' }}>
                            <span style={{ fontSize: 12, color: 'var(--body)' }}>{a.artistKo || a.artist}</span>
                            {a.artistKo && <span style={{ fontSize: 10, color: 'var(--sub)', marginLeft: 6 }}>({a.artist})</span>}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
              ) : (
                <>
                <VintageFrame>
                  <div onClick={() => fileRef.current?.click()}
                    onDrop={e => { e.preventDefault(); setImg(e.dataTransfer.files[0]) }}
                    onDragOver={e => e.preventDefault()}
                    style={{ width: '100%', height: '100%', background: 'transparent', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <div style={{ textAlign: 'center', padding: '20px 16px' }}>
                      <div style={{ fontSize: 28, marginBottom: 12, opacity: 0.5, letterSpacing: 6, fontFamily: 'serif', color: 'var(--gold3)', fontWeight: 300 }}>+</div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--body)', marginBottom: 8, lineHeight: 1.5, letterSpacing: 0.3 }}>감상할 작품을 액자 안에 놓아주세요</div>
                      <div style={{ fontSize: 11, color: 'var(--sub)', lineHeight: 1.7 }}>이미지를 클릭하거나 드래그해 업로드하세요</div>
                      <div style={{ fontSize: 9, color: 'rgba(154,120,80,0.40)', marginTop: 8, letterSpacing: 2 }}>JPG · PNG · WEBP 지원</div>
                    </div>
                  </div>
                </VintageFrame>
                <button className="btn-primary" style={{ marginTop: 12 }} onClick={() => fileRef.current?.click()}>
                  이미지 파일 열기
                </button>
                <button className="btn-outline" onClick={() => {
                  setResult({
                    artwork_image: "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                    saliency_image: "",
                    thumbnail: "",
                    info: {
                      title: "",
                      artist: "",
                      year: "",
                      medium: "",
                      ui_message: ""
                    },
                    color: {
                      dominant_colors: [],
                      warm_color_ratio: 0,
                      cool_color_ratio: 0,
                      average_brightness: 0,
                      brightness_label: "",
                      average_saturation: 0,
                      saturation_label: "",
                      contrast_level: 0,
                      contrast_label: "",
                      color_moods_ko: []
                    },
                    comp: {
                      composition_analysis: "",
                      composition_score: 0
                    },
                    person: {
                      detected_people_count: 0,
                      poses: [],
                      emotional_posture_ko: []
                    },
                    scores: {},
                    evidence: [],
                    essay: {
                      title: "",
                      body: [],
                      questions: [],
                      comfort: ""
                    },
                    quality: {},
                    candidates: [],
                    identification_status: "unknown",
                    ocr_info: {},
                    figure: {},
                    similar: []
                  });
                  nav('/results');
                }} style={{ marginTop: 8, height: 34, fontSize: 10, letterSpacing: '1.5px', background: 'rgba(194,166,136,0.05)', color: 'var(--gold2)' }}>
                  데모 명화로 즉시 분석하기 (검증용)
                </button>
              </>
            )}
            <input ref={fileRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={e => setImg(e.target.files[0])} />
          </>
        )}

        <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, var(--line), transparent)', margin: '4px 0' }} />

        {/* Analysis options */}
        {!preview && (
          <p style={{ textAlign: 'center', fontSize: 10, color: 'rgba(154,120,80,0.40)', letterSpacing: 0.5, padding: '6px 0' }}>
            이미지를 업로드하면 감상 설정을 선택할 수 있어요
          </p>
        )}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, opacity: preview ? 1 : 0.38, pointerEvents: preview ? 'auto' : 'none', transition: 'opacity 0.25s' }}>

          {/* 작품 유형 */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
              <div style={{ fontFamily: "'Noto Serif KR', serif", fontSize: 11.5, fontWeight: 700, color: 'var(--gold2)', letterSpacing: 1 }}>작품 유형</div>
              <div style={{ fontSize: 9, color: 'rgba(154,120,80,0.50)', letterSpacing: 0.5 }}>하나만 선택</div>
            </div>
            <p style={{ fontSize: 9.5, color: 'rgba(154, 120, 80, 0.45)', marginBottom: 8, lineHeight: 1.5, letterSpacing: 0.2 }}>
              유형을 선택하면 분석 방향이 더 정확해져요. 잘 모르겠다면 자동 추천을 선택하세요.
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {[['자동', '자동 추천'], ['인물', '인물'], ['풍경', '풍경'], ['추상', '추상'], ['정물', '정물'], ['건축', '건축']].map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setArtworkType(key)}
                  className={`option-chip ${artworkType === key ? 'active' : ''}`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* 분석 초점 */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <div style={{ fontFamily: "'Noto Serif KR', serif", fontSize: 11.5, fontWeight: 700, color: 'var(--gold2)', letterSpacing: 1 }}>분석 초점</div>
              <div style={{ fontSize: 9, color: 'rgba(154,120,80,0.50)', letterSpacing: 0.5 }}>여러 개 선택 가능</div>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {['전체', '색감', '구도', '분위기', '인물·장면', '감정 회고'].map(f => {
                const on = analysisFocus.includes(f)
                return (
                  <button
                    key={f}
                    onClick={() => toggleFocus(f)}
                    className={`option-chip ${on ? 'active' : ''}`}
                  >
                    {f}
                  </button>
                )
              })}
            </div>
          </div>

          {/* 해설 스타일 */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <div style={{ fontFamily: "'Noto Serif KR', serif", fontSize: 11.5, fontWeight: 700, color: 'var(--gold2)', letterSpacing: 1 }}>해설 스타일</div>
              <div style={{ fontSize: 9, color: 'rgba(154,120,80,0.50)', letterSpacing: 0.5 }}>하나만 선택</div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 6, marginBottom: 8 }}>
              {[
                { key: 'healing',  label: '아트 테라피',   sub: 'Art Therapy' },
                { key: 'docent',   label: '도슨트 해설',   sub: 'Docent' },
                { key: 'analysis', label: '시각 분석',     sub: 'Analysis' },
                { key: 'short',    label: '짧은 감상',     sub: 'Brief' },
              ].map(({ key, label, sub }) => {
                const on = selectedMode === key
                return (
                  <button
                    key={key}
                    onClick={() => setSelectedMode(key)}
                    className={`option-card ${on ? 'active' : ''}`}
                  >
                    <span className="card-check">✓</span>
                    <span className="card-label">{label}</span>
                    <span className="card-sub">{sub}</span>
                  </button>
                )
              })}
            </div>
            {/* 실시간 스타일 동적 가이드 설명 */}
            <p style={{ fontSize: 9.5, color: 'rgba(154, 120, 80, 0.45)', lineHeight: 1.5, letterSpacing: 0.2 }}>
              {selectedMode === 'healing' && '색채와 여백이 남기는 감각을 따라, 마음을 차분히 돌아보는 따뜻한 감상문을 제공합니다.'}
              {selectedMode === 'docent' && '화가의 삶과 시대의 이야기를 바탕으로, 작품을 더 깊고 입체적으로 바라보는 해설을 제공합니다.'}
              {selectedMode === 'analysis' && '명도·채도·구도·공간감 등 눈에 보이는 요소를 정밀하게 짚고, 그 시각적 작용을 해석합니다.'}
              {selectedMode === 'short' && '가장 인상적인 요소 하나에 집중해, 짧고 선명한 감상과 한 줄 문장을 전합니다.'}
            </p>
          </div>

          {/* Recommended shortcut */}
          {preview && (
            <button
              onClick={applyRecommended}
              className="btn-outline"
              style={{ height: 34, fontSize: 10, letterSpacing: '1px', display: 'block', width: '100%', marginTop: 6 }}
            >
              추천 설정으로 초기화
            </button>
          )}

        </div>

        {/* Pre-emotion selection */}
        <div style={{ opacity: preview ? 1 : 0.38, pointerEvents: preview ? 'auto' : 'none', transition: 'opacity 0.25s' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <div style={{ fontFamily: "'Noto Serif KR', serif", fontSize: 11.5, fontWeight: 700, color: 'var(--gold2)', letterSpacing: 1 }}>감상 전 마음</div>
            <div style={{ fontSize: 9, color: 'rgba(154,120,80,0.50)', letterSpacing: 0.5 }}>선택 사항</div>
          </div>
          <p style={{ fontSize: 9.5, color: 'rgba(154, 120, 80, 0.45)', marginBottom: 10, lineHeight: 1.5, letterSpacing: 0.2 }}>
            지금 마음과 가까운 단어가 있다면 골라보세요. 감상 완료 후 감정 변화를 함께 분석해 드립니다.
          </p>
          {!showAllEmotions ? (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7 }}>
              {DEFAULT_EMOTIONS.map(e => (
                <button key={e} onClick={() => toggleEmo(e)} className={`option-chip ${myEmotion.includes(e) ? 'active' : ''}`}>{e}</button>
              ))}
              {myEmotion.filter(e => e !== '건너뜀' && !DEFAULT_EMOTIONS.includes(e)).map(e => (
                <button key={`sel-${e}`} onClick={() => toggleEmo(e)} className="option-chip active">{e}</button>
              ))}
              <button onClick={() => setShowAllEmotions(true)} style={{ padding: '7px 12px', borderRadius: 2, fontSize: 11, fontFamily: 'inherit', cursor: 'pointer', letterSpacing: 0.5, border: '1px dashed rgba(154,120,80,0.35)', background: 'transparent', color: 'rgba(154,120,80,0.6)' }}>더 세밀한 감정 선택 ›</button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {EMOTION_CATEGORIES.map(cat => (
                <div key={cat.label}>
                  <p style={{ fontSize: 9, color: 'var(--gold3)', fontWeight: 700, letterSpacing: 2, marginBottom: 8 }}>{cat.label}</p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7 }}>
                    {cat.emotions.map(e => (
                      <button key={e} onClick={() => toggleEmo(e)} className={`option-chip ${myEmotion.includes(e) ? 'active' : ''}`}>{e}</button>
                    ))}
                  </div>
                </div>
              ))}
              <button onClick={() => setShowAllEmotions(false)} style={{ alignSelf: 'flex-start', padding: '5px 10px', fontSize: 10, fontFamily: 'inherit', cursor: 'pointer', letterSpacing: 0.5, border: '1px solid rgba(154,120,80,0.25)', borderRadius: 2, background: 'transparent', color: 'rgba(154,120,80,0.5)' }}>접기 ↑</button>
            </div>
          )}
          <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 10 }}>
            {myEmotion.length > 0 ? (
              <button onClick={() => setMyEmotion([])} style={{
                background: 'transparent', border: '1px solid rgba(100,40,60,0.35)', borderRadius: 2,
                padding: '4px 10px', fontSize: 10, color: 'rgba(180,100,120,0.5)', cursor: 'pointer', fontFamily: 'inherit', letterSpacing: 0.5,
              }}>초기화</button>
            ) : (
              <button onClick={() => setMyEmotion(['건너뜀'])} style={{
                background: 'transparent', border: '1px solid rgba(100,40,60,0.35)', borderRadius: 2,
                padding: '4px 10px', fontSize: 10, color: 'rgba(180,100,120,0.45)', cursor: 'pointer', fontFamily: 'inherit', letterSpacing: 0.5,
              }}>잘 모르겠어요</button>
            )}
          </div>
        </div>

        {error && <p style={{ color: '#D47070', fontSize: 12, textAlign: 'center' }}>{error}</p>}

        {/* Settings summary + button */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {preview && (
            <div style={{ padding: '8px 14px', background: 'rgba(154,120,80,0.07)', border: '1px solid rgba(154,120,80,0.22)', borderRadius: 3 }}>
              <p style={{ fontSize: 8, color: 'rgba(154,120,80,0.55)', letterSpacing: 2, fontWeight: 700, marginBottom: 4 }}>분석 설정</p>
              <p style={{ fontSize: 11, color: 'var(--body)', letterSpacing: 0.3, lineHeight: 1.6 }}>{settingsSummary}</p>
            </div>
          )}
          {!file && (
            <p style={{ fontSize: 11, color: 'rgba(154,120,80,0.45)', textAlign: 'center', letterSpacing: 0.3 }}>
              작품 이미지를 업로드하면 감상 여정을 시작할 수 있어요
            </p>
          )}
          <button className="btn-primary" onClick={handleAnalyzeClick} disabled={!file} style={{ height: 54, fontSize: 15, letterSpacing: 2 }}>
            감상 여정 시작하기
          </button>
        </div>

        {/* 작품 후보 확인 모달 */}
        {showConfirm && (
          <div style={{ position: 'fixed', inset: 0, zIndex: 200, background: 'rgba(28,20,12,0.65)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
            <div style={{ width: '100%', maxWidth: 360, background: 'var(--card)', border: '1px solid var(--line)', borderRadius: 6, padding: '24px 20px', display: 'flex', flexDirection: 'column', gap: 12 }}>
              <p style={{ fontSize: 11, color: 'var(--gold3)', letterSpacing: 2, fontWeight: 700 }}>혹시 이 작품인가요?</p>
              <p style={{ fontSize: 11, color: 'var(--sub)', lineHeight: 1.7 }}>
                입력하신 정보와 비슷한 작품을 찾았어요.<br />
                가장 가까운 작품을 선택해주세요.
              </p>
              {confirmCands.map(a => (
                <button key={a.id} onClick={() => { setShowConfirm(false); doAnalyze(a.title, a.artist) }}
                  style={{ width: '100%', textAlign: 'left', background: 'var(--card2)', border: '1px solid var(--line)', borderRadius: 4, padding: '12px 14px', cursor: 'pointer', fontFamily: 'inherit', transition: 'border-color 0.15s' }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = 'rgba(184,145,42,0.45)'}
                  onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--line)'}
                >
                  {a.titleKo
                    ? <div style={{ fontSize: 13, color: 'var(--body)', marginBottom: 2 }}>{a.titleKo}{a.year ? ` (${a.year})` : ''}</div>
                    : <div style={{ fontSize: 13, color: 'var(--body)', marginBottom: 2 }}>{a.title}{a.year ? ` (${a.year})` : ''}</div>
                  }
                  {a.titleKo && <div style={{ fontSize: 11, color: 'var(--sub)', marginBottom: 3 }}>{a.title}</div>}
                  <div style={{ fontSize: 10, color: 'var(--gold2)' }}>{a.artistKo ? `${a.artistKo} (${a.artist})` : a.artist}</div>
                </button>
              ))}
              <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                <button className="btn-ghost" style={{ flex: 1, fontSize: 11, height: 40 }} onClick={() => { setShowConfirm(false); doAnalyze(rawTitle || hintTitle, rawArtist || hintArtist) }}>
                  입력한 정보 그대로
                </button>
                <button className="btn-ghost" style={{ flex: 1, fontSize: 11, height: 40 }} onClick={() => { setShowConfirm(false); doAnalyze('', '') }}>
                  정보 없이 분석
                </button>
              </div>
            </div>
          </div>
        )}

        <p style={{ textAlign: 'center', fontSize: 10, color: 'rgba(122,92,56,0.50)', lineHeight: 1.9, letterSpacing: 0.3 }}>
          이 해설은 심리 진단이 아닌 감상과 자기 회고를 위한 참고입니다
        </p>
      </div>
    </div>
  )
}
