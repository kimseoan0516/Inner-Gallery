import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApp } from '../context/AppContext.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { saveJournal, docentChat, getArtworkEra, generateEssayText } from '../api.js'
import GoldDivider from '../components/GoldDivider.jsx'
import PaletteBar  from '../components/PaletteBar.jsx'
import EmotionBar  from '../components/EmotionBar.jsx'
import LoginModal  from '../components/LoginModal.jsx'
import { ARTWORK_DB } from '../data/artworks.js'

// ── HSL → Hex 변환 ──────────────────────────────────────────
function hslToHex(h, s, l) {
  h = h % 360; s /= 100; l /= 100
  const a = s * Math.min(l, 1 - l)
  const f = n => {
    const k = (n + h / 30) % 12
    const c = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1)
    return Math.round(255 * c).toString(16).padStart(2, '0')
  }
  return `#${f(0)}${f(8)}${f(4)}`
}

// ── 한글 / 영문 혼합 표시 헬퍼 ─────────────────────────────
const formatTitle = (titleText) => {
  if (!titleText) return '';
  const cleanTitle = titleText.replace(/\s*\(.*?\)\s*/g, '').trim().toLowerCase();
  const found = ARTWORK_DB.find(
    (item) =>
      item.title?.toLowerCase() === cleanTitle ||
      item.titleKo?.toLowerCase() === cleanTitle ||
      item.titleAlias?.some((alias) => alias.toLowerCase() === cleanTitle)
  );
  if (found) {
    return `${found.titleKo} (${found.title})`;
  }
  return titleText;
};

const formatArtist = (artistText) => {
  if (!artistText) return '';
  const cleanArtist = artistText.replace(/\s*\(.*?\)\s*/g, '').trim().toLowerCase();
  const found = ARTWORK_DB.find(
    (item) =>
      item.artist?.toLowerCase() === cleanArtist ||
      item.artistKo?.toLowerCase() === cleanArtist ||
      item.artistAlias?.some((alias) => alias.toLowerCase() === cleanArtist)
  );
  if (found) {
    return `${found.artistKo} (${found.artist})`;
  }
  return artistText;
};


function SectionHead({ icon, title, en }) {
  return (
    <div style={{ marginBottom: 2 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
        <span style={{ fontSize: 13, color: 'var(--gold2)', lineHeight: 1 }}>{icon}</span>
        <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)' }}>{title}</span>
      </div>
      {en && <p style={{ fontSize: 10, color: 'var(--sub)', fontStyle: 'italic', letterSpacing: 1.5, marginLeft: 21, marginBottom: 6 }}>{en}</p>}
      <GoldDivider />
    </div>
  )
}

/* ── Essay keyword highlighter ─────────────────────────────
   - Quoted text (「」'" ") → antique gold, semi-bold
   - Core art/visual/emotion terms → bright ivory, bold
   Everything else stays as normal --body text.
──────────────────────────────────────────────────────────── */
const ART_KEYWORDS = [
  '색채','색상','색조','팔레트','빛','그림자','명암','밝기','채도','대비',
  '구도','여백','대칭','균형','원근','시선','구성',
  '질감','붓터치','기법','화법','필치',
  '분위기','인상','정서','감성','감정',
  '표정','자세','포즈','시선',
  '공간','형태','선','점',
]
const ART_KW_RE = new RegExp(`(${ART_KEYWORDS.join('|')})`, 'g')
const QUOTE_RE  = /([「『「'"'][^「』""'\n]{1,60}?[」』""'"])/g

function renderHighlightedParagraph(text, idx) {
  if (!text) return '';
  const combined = /(\*\*(.*?)\*\*)|([「『][^「』\n]{1,100}?[」』])/g;
  const result = [];
  let last = 0;
  let m;
  while ((m = combined.exec(text)) !== null) {
    if (m.index > last) {
      result.push(text.slice(last, m.index));
    }
    if (m[1]) {
      // Markdown bold phrase — underline highlight (most important sentences)
      result.push(
        <span key={`b-${m.index}`} style={{
          color: 'var(--text)', fontWeight: 700,
          textDecorationLine: 'underline',
          textDecorationStyle: 'solid',
          textDecorationColor: 'rgba(154,120,50,0.45)',
          textUnderlineOffset: '3px',
          textDecorationThickness: '1.5px',
        }}>
          {m[2]}
        </span>
      );
    } else if (m[3]) {
      // Quoted/bracketed core sentence — warm highlight
      result.push(
        <span key={`q-${m.index}`} style={{
          color: 'var(--gold2)', fontWeight: 600, fontStyle: 'normal',
          background: 'rgba(184,145,42,0.09)',
          padding: '1px 3px',
          borderRadius: 3,
        }}>
          {m[3]}
        </span>
      );
    }
    last = combined.lastIndex;
  }
  if (last < text.length) {
    result.push(text.slice(last));
  }
  return result;
}

/* Corner-bracket essay card */
function EssayCard({ title, en, children }) {
  const B = 'rgba(159,122,47,0.22)'
  const L = 14, T = 7
  return (
    <div style={{ position: 'relative', background: 'var(--card)', border: '1px solid var(--line)', borderRadius: 8, padding: '24px 22px' }}>
      {/* corners — subtle only */}
      {[
        { top: T, left: T, borderTop: `1px solid ${B}`, borderLeft: `1px solid ${B}` },
        { top: T, right: T, borderTop: `1px solid ${B}`, borderRight: `1px solid ${B}` },
        { bottom: T, left: T, borderBottom: `1px solid ${B}`, borderLeft: `1px solid ${B}` },
        { bottom: T, right: T, borderBottom: `1px solid ${B}`, borderRight: `1px solid ${B}` },
      ].map((s, i) => (
        <div key={i} style={{ position: 'absolute', width: L, height: L, pointerEvents: 'none', ...s }} />
      ))}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
        <span style={{ fontSize: 10, color: 'var(--gold2)', letterSpacing: 2 }}>◆</span>
        <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)' }}>{title}</span>
      </div>
      <p style={{ fontSize: 10, color: 'var(--sub)', fontStyle: 'italic', letterSpacing: 1.5, marginLeft: 20, marginBottom: 10 }}>{en}</p>
      <GoldDivider />
      <div style={{ marginTop: 18 }}>{children}</div>
    </div>
  )
}

const EMOTION_CATEGORIES = [
  { label: '가라앉음',         emotions: ['슬픔', '외로움', '그리움', '공허함', '결핍', '상처', '자괴감', '절망', '무기력', '지침', '부담감'] },
  { label: '불안과 흔들림',     emotions: ['불안', '긴장감', '두려움', '막연함', '내적 갈등'] },
  { label: '분노와 복잡한 감정', emotions: ['짜증', '화', '증오', '애증'] },
  { label: '안정과 위로',       emotions: ['평온함', '편안함', '여유', '휴식', '온기', '위로', '수용', '화해', '환기'] },
  { label: '회복과 긍정',       emotions: ['회복', '긍정감', '희망', '기쁨', '설렘', '기대', '자신감', '열정', '생기', '자유로움', '풍족함', '영감'] },
  { label: '깊은 감각과 바라봄', emotions: ['감동', '경이로움', '황홀감', '성찰', '집중', '깨달음', '이해', '배려심', '호기심', '통찰'] },
]
const DEFAULT_EMOTIONS = ['슬픔', '외로움', '지침', '불안', '긴장감', '짜증', '평온함', '온기', '희망', '기쁨', '설렘', '이해', '감동', '경이로움']

const MOOD_COLORS = [
  { hex: '#5EB0AA', name: '청록색',       mood: '평온함' },
  { hex: '#E5C5B3', name: '베이지색',     mood: '따뜻함' },
  { hex: '#E388A3', name: '분홍색',       mood: '설렘'   },
  { hex: '#F5C352', name: '노란색',       mood: '기쁨'   },
  { hex: '#AEA0DC', name: '연보라색',     mood: '그리움' },
  { hex: '#798FA8', name: '흐린 파란색',   mood: '쓸쓸함' },
  { hex: '#4E5B6E', name: '어두운 회청색', mood: '불안함' },
  { hex: '#DF3A48', name: '붉은색',       mood: '강렬함' },
]

export default function Results() {
  const nav = useNavigate()
  const { result, preEmotion } = useApp()
  const { user } = useAuth()
  const [reflection,   setReflection]   = useState('')
  const [saved,        setSaved]        = useState(false)
  const [savedDate,    setSavedDate]    = useState('')
  const [saving,       setSaving]       = useState(false)
  const [showToast,    setShowToast]    = useState('')
  const [showLoginModal, setShowLoginModal] = useState(false)
  const pendingEntry = useRef(null)
  const [postEmotion,  setPostEmotion]  = useState([])
  const [moodColor,       setMoodColor]       = useState(null)
  const [moodColorTab,    setMoodColorTab]    = useState('preset')
  const [customHex,       setCustomHex]       = useState('#C8B4A0')
  const [customColorName, setCustomColorName] = useState('')
  const [moodNote,        setMoodNote]        = useState('')
  const [hueVal,          setHueVal]          = useState(0)
  const [satVal,          setSatVal]          = useState(60)
  const [litVal,          setLitVal]          = useState(55)
  // 작품의 시대와 이야기
  const [eraOpen,    setEraOpen]    = useState(false)
  const [eraData,    setEraData]    = useState(null)
  const [eraLoading, setEraLoading] = useState(false)
  const [eraError,   setEraError]   = useState('')
  // Recognition correction
  const [correcting,   setCorrecting]   = useState(false)
  const [manualTitle,  setManualTitle]  = useState('')
  const [manualArtist, setManualArtist] = useState('')
  const [correctedInfo, setCorrectedInfo] = useState(null)
  const [correctedEssay, setCorrectedEssay] = useState(null)
  const [essayLoading, setEssayLoading] = useState(false)
  const [showAllPost, setShowAllPost] = useState(false)
  const [questionAnswers, setQuestionAnswers] = useState({})
  const [openQuestion, setOpenQuestion] = useState(null)
  // Docent chat
  const [chatOpen,  setChatOpen]  = useState(false)
  const [chatMsg,   setChatMsg]   = useState('')
  const [chatLog,   setChatLog]   = useState([])
  const [chatLoading, setChatLoading] = useState(false)
  const chatEndRef = useRef(null)
  const chatCardRef = useRef(null)

  useEffect(() => {
    if (!result) {
      nav('/')
    }
  }, [result, nav])

  if (!result) return null

  const { artwork_image, saliency_image, thumbnail, info = {}, color = {}, comp = {}, person = {}, scores = {}, evidence = [], essay = {}, quality = {}, candidates = [], identification_status, ocr_info = {}, figure = {}, similar = [] } = result
  const moodTags = [...(color?.color_moods_ko || []), ...(person?.emotional_posture_ko || [])]
  const paletteColors = (color?.dominant_colors || []).slice(0, 5).map(c => {
    const rgbVal = Array.isArray(c?.rgb) ? c.rgb : [0, 0, 0];
    return {
      hex: '#' + rgbVal.map(v => Math.round(Number(v) || 0).toString(16).padStart(2, '0')).join(''),
      name: c?.name || '작품색',
      mood: '',
    };
  })

  const togglePost = (e) => setPostEmotion(prev =>
    prev.includes(e) ? prev.filter(x => x !== e) : [...prev, e]
  )

  const displayInfo = correctedInfo || info
  const activeEssay = correctedEssay || essay

  // 한줄 요약(제목)이 본문 첫 줄에 들어오는 모든 패턴을 분리
  const { derivedEssayTitle, essayDisplayBody } = (() => {
    let title = (activeEssay.title || '').trim()
    let body = [...(activeEssay.body || [])]

    const stripMd = s => s.replace(/\*\*/g, '').replace(/^\*|\*$/g, '').trim()
    const isSentenceEnding = s => /[.。!?]$/.test(s) || /[다요어아죠네요]$/.test(stripMd(s))

    if (body.length > 0) {
      const first = body[0].trim()
      const clean = stripMd(first)

      // ① 마크다운 볼드: **제목**
      const boldMatch = first.match(/^\*\*(.*?)\*\*$/)
      // ② 이탤릭: *제목*
      const italicMatch = !boldMatch && first.match(/^\*(.*?)\*$/)
      // ③ 레이블 접두어: 한줄 요약: / 요약: / 제목:
      const labelMatch = /^\*\*?(한\s*줄\s*요\s*약|요\s*약|제\s*목)\s*:\s*\*\*?/i.test(first) ||
                         /^(한\s*줄\s*요\s*약|요\s*약|제\s*목)\s*:/i.test(first)
      // ④ 짧은 시적 표현 — 35자 이하 & 문장종결어미로 끝나지 않음
      const isShortTitle = !title && clean.length > 0 && clean.length <= 35 && !isSentenceEnding(clean)

      if (boldMatch) {
        if (!title) title = boldMatch[1].trim()
        body = body.slice(1)
      } else if (italicMatch) {
        if (!title) title = italicMatch[1].trim()
        body = body.slice(1)
      } else if (labelMatch) {
        if (!title) title = first
          .replace(/^\*\*?(한\s*줄\s*요\s*약|요\s*약|제\s*목)\s*:\s*\*\*?/i, '')
          .replace(/^(한\s*줄\s*요\s*약|요\s*약|제\s*목)\s*:/i, '')
          .replace(/\*\*/g, '').trim()
        body = body.slice(1)
      } else if (isShortTitle) {
        title = clean
        body = body.slice(1)
      }

      // 중복 제거: body 남은 첫 줄이 title과 동일하면 제거
      if (title && body.length > 0) {
        const cleanFirst = stripMd(body[0].trim())
        const cleanTitle = stripMd(title)
        if (cleanFirst === cleanTitle || (cleanFirst.includes(cleanTitle) && cleanFirst.length < cleanTitle.length + 15)) {
          body = body.slice(1)
        }
      }
    }
    return { derivedEssayTitle: title, essayDisplayBody: body }
  })()
  // 작품명/화가를 "확정"해서 보여주거나 저장/대화에 쓰지 않도록 안전장치
  // - LLM/후보가 추정한 신원을 사용자가 확인하지 않은 경우, 이름을 숨긴다.
  const identityConfirmed =
    Boolean(correctedInfo?.title && correctedInfo?.artist) ||
    (identification_status === 'confirmed' && Boolean(displayInfo?.title && displayInfo?.artist))

  const safeInfo = identityConfirmed
    ? displayInfo
    : { title: '', artist: '', year: '', medium: '' }

  const applyCorrection = async () => {
    if (!manualTitle && !manualArtist) return
    const newInfo = { ...info, title: manualTitle || info.title, artist: manualArtist || info.artist }
    setCorrectedInfo(newInfo)
    setCorrecting(false)
    setEssayLoading(true)
    try {
      const { essay: newEssay } = await generateEssayText({
        title:  newInfo.title,
        artist: newInfo.artist,
        year:   newInfo.year || '',
        mode:   'healing',
      })
      if (newEssay?.body?.length > 0) setCorrectedEssay(newEssay)
    } catch {
      // keep original essay on error
    } finally {
      setEssayLoading(false)
    }
  }

  const sendChat = async () => {
    if (!chatMsg.trim() || chatLoading) return
    const msg = chatMsg.trim()
    setChatMsg('')
    setChatLog(l => [...l, { role: 'user', text: msg }])
    setChatLoading(true)
    try {
      const { reply } = await docentChat({
        artwork_info: { title: safeInfo.title, artist: safeInfo.artist, year: safeInfo.year },
        message: msg,
      })
      setChatLog(l => [...l, { role: 'ai', text: reply }])
      setTimeout(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
        chatCardRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
      }, 80)
    } catch {
      setChatLog(l => [...l, { role: 'ai', text: '죄송합니다, 잠시 후 다시 시도해주세요.' }])
    } finally {
      setChatLoading(false)
    }
  }

  const handleChatToggle = () => {
    const next = !chatOpen
    setChatOpen(next)
    if (next) {
      setTimeout(() => {
        chatCardRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 60)
    }
  }

  const buildEntry = () => {
    const now = new Date()
    const pad = n => String(n).padStart(2, '0')
    const localDateStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`
    return {
    date:             localDateStr,
    reflection,
    artwork_title:    identityConfirmed ? (formatTitle(safeInfo.title)  || '')  : '',
    artwork_artist:   identityConfirmed ? (formatArtist(safeInfo.artist) || '')  : '',
    artwork_year:     identityConfirmed ? (safeInfo.year   || '')  : '',
    essay_title:      identityConfirmed ? (activeEssay.title || '') : '이름을 알 수 없는 작품',
    essay_body:       activeEssay.body     || [],
    questions:        activeEssay.questions || [],
    comfort:          activeEssay.comfort   || '',
    moods:            moodTags.slice(0, 10),
    dominant_colors:  (color.dominant_colors || []).slice(0, 5).map(c => ({
      rgb: c.rgb, name: c.name || '', percentage: c.percentage ?? 0.2,
    })),
    thumbnail:        thumbnail || '',
    pre_emotions:     preEmotion  || [],
    post_emotions:    postEmotion || [],
    mood_color:       moodColor?.hex || '',
    mood_color_name:  moodColor
      ? (moodColorTab === 'custom' && customColorName.trim())
        ? customColorName.trim()
        : `${moodColor.name}${moodColor.mood ? ' · ' + moodColor.mood : ''}`
      : '',
    mood_note:        moodNote,
    era_data:         (eraData && !eraData._no_era && !eraData._not_in_db && !eraData._error)
                        ? JSON.stringify(eraData) : '',
    question_answers: JSON.stringify(questionAnswers),
  }
  }

  const doSave = async (entry) => {
    setSaving(true)
    try {
      await saveJournal(entry)
      setSaved(true)
      setSavedDate(entry.date)
      setShowToast('감상이 저장되었어요')
      setTimeout(() => setShowToast(''), 2500)
    } catch {
      setShowToast('저장에 실패했어요. 다시 시도해주세요.')
      setTimeout(() => setShowToast(''), 1800)
    } finally {
      setSaving(false)
    }
  }

  const handleSave = () => {
    if (saving) return
    const entry = buildEntry()
    if (!user) {
      pendingEntry.current = entry
      setShowLoginModal(true)
      return
    }
    doSave(entry)
  }

  const handleLoginSuccess = () => {
    setShowLoginModal(false)
    if (pendingEntry.current) {
      doSave(pendingEntry.current)
      pendingEntry.current = null
    }
  }

  const idStatus = correctedInfo
    ? (identityConfirmed ? 'confirmed' : 'unknown')
    : (identityConfirmed ? 'confirmed' : 'unknown')

  const fetchEra = async () => {
    if (eraLoading) return
    if (eraData && !eraError) return  // already have good data
    setEraLoading(true); setEraError(''); setEraData(null)
    try {
      const d = await getArtworkEra({
        title:                safeInfo.title  || '',
        artist:               safeInfo.artist || '',
        year:                 safeInfo.year   || '',
        identificationStatus: idStatus,
        visualContext: {
          dominant_colors: (color.dominant_colors || []).map(c => c.name || '').filter(Boolean),
          color_moods:     color.color_moods_ko || [],
          brightness:      color.brightness_label || '',
        },
      })
      if (d._error) {
        setEraError('시대 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.')
      } else {
        setEraData(d)
      }
    } catch {
      setEraError('정보를 불러오는 중 오류가 발생했습니다')
    } finally {
      setEraLoading(false)
    }
  }

  const handleEraToggle = () => {
    const next = !eraOpen
    setEraOpen(next)
    if (next && !eraData && !eraLoading) fetchEra()
  }

  const evEmotions = new Set(evidence.map(e => e.emotion))
  const restScores = Object.entries(scores).filter(([lbl]) => !evEmotions.has(lbl)).sort(([,a],[,b]) => b-a)

  return (
    <div className="screen" style={{ background: 'var(--bg)' }}>
      {showLoginModal && (
        <LoginModal
          onSuccess={handleLoginSuccess}
          onClose={() => setShowLoginModal(false)}
        />
      )}
      {/* Fixed header */}
      <div className="nav-bar" style={{ background: 'var(--card)', borderBottom: '1px solid var(--line)' }}>
        <button className="btn-ghost" onClick={() => nav(-1)}>←</button>
        <div style={{ flex: 1, textAlign: 'center' }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)', letterSpacing: 0.5 }}>작품 감상</div>
          <div style={{ fontSize: 9, color: 'var(--gold)', fontStyle: 'italic', letterSpacing: 1.5 }}>Art Appreciation</div>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          style={{
            background: 'transparent',
            color: 'var(--body)',
            border: '1px solid rgba(194, 166, 136, 0.28)',
            borderRadius: '4px',
            padding: '4px 12px',
            height: '30px',
            fontSize: '12px',
            fontWeight: '500',
            cursor: saving ? 'not-allowed' : 'pointer',
            fontFamily: 'inherit',
            transition: 'all 0.15s ease',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            letterSpacing: '0.5px'
          }}
          onMouseEnter={(e) => {
            if (saving) return
            e.currentTarget.style.borderColor = 'rgba(194, 166, 136, 0.55)'
            e.currentTarget.style.color = 'var(--text)'
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)'
          }}
          onMouseLeave={(e) => {
            if (saving) return
            e.currentTarget.style.borderColor = 'rgba(194, 166, 136, 0.28)'
            e.currentTarget.style.color = 'var(--body)'
            e.currentTarget.style.background = 'transparent'
          }}
        >
          {saved ? '✓' : (saving ? '저장 중' : '저장')}
        </button>
      </div>
      {/* Toast notification */}
      {showToast && (
        <div style={{
          position: 'fixed', top: 20, left: '50%', transform: 'translateX(-50%)',
          background: 'rgba(28,20,12,0.82)', color: 'var(--card2)', padding: '8px 16px',
          borderRadius: 4, fontSize: 12, zIndex: 200, animation: 'fadeIn 0.3s, fadeOut 0.3s 1.7s',
          border: '1px solid rgba(184,145,42,0.25)',
        }}>{showToast}</div>
      )}

      <div className="screen-scroll" style={{ padding: '20px 20px 52px', display: 'flex', flexDirection: 'column', gap: 22 }}>



        {/* Artwork image — full width, no frame */}
        <div style={{ borderRadius: 6, overflow: 'hidden', background: 'var(--card2)', border: '1px solid var(--line)' }}>
          <img
            src={`data:image/jpeg;base64,${artwork_image}`}
            alt="작품"
            style={{ width: '100%', height: 'auto', display: 'block', maxHeight: 500, objectFit: 'contain' }}
          />
        </div>

        {/* Artwork info card */}
        <div className="card" style={{ padding: '24px 22px', display: 'flex', gap: 16, alignItems: 'flex-start' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            {safeInfo.artist && (
              <p style={{ fontSize: 12, color: 'rgba(70,52,40,0.58)', marginBottom: 10, letterSpacing: 0.2 }}>{formatArtist(safeInfo.artist)}</p>
            )}
            {identityConfirmed ? (() => {
              const clean = (safeInfo.title || '').replace(/\s*\(.*?\)\s*/g, '').trim().toLowerCase()
              const found = ARTWORK_DB.find(item =>
                item.title?.toLowerCase() === clean ||
                item.titleKo?.toLowerCase() === clean ||
                item.titleAlias?.some(a => a.toLowerCase() === clean)
              )
              const titleKo = found?.titleKo
              const titleEn = found?.title || safeInfo.title
              return (
                <>
                  <p style={{ fontSize: 20, fontWeight: 700, fontFamily: "'Noto Serif KR', serif", color: 'var(--text)', lineHeight: 1.32, letterSpacing: '-0.3px', marginBottom: 6 }}>
                    {titleKo || titleEn || '작품 분석 결과'}
                  </p>
                  {titleKo && titleEn && (
                    <p style={{ fontSize: 12, color: 'rgba(70,52,40,0.50)', fontStyle: 'italic', marginBottom: 14, letterSpacing: 0.1, lineHeight: 1.4 }}>
                      {titleEn}
                    </p>
                  )}
                </>
              )
            })() : (
              <p style={{ fontSize: 20, fontWeight: 700, fontFamily: "'Noto Serif KR', serif", color: 'var(--text)', lineHeight: 1.32, marginBottom: 6 }}>
                이름을 알 수 없는 작품
              </p>
            )}
            {/* 한줄 감상 제목 — 작품 정보와 명확히 분리 */}
            {derivedEssayTitle && (
              <div style={{ marginTop: 12, paddingTop: 10, borderTop: '1px solid rgba(184,145,42,0.15)' }}>
                <p style={{ fontSize: 13, color: 'var(--gold2)', lineHeight: 1.65, letterSpacing: 0.2, fontFamily: "'Noto Serif KR', serif", fontStyle: 'italic' }}>
                  {derivedEssayTitle}
                </p>
              </div>
            )}
            {safeInfo.year && (
              <p style={{ fontSize: 11, color: 'rgba(70,52,40,0.38)', marginTop: 8 }}>{safeInfo.year}</p>
            )}
          </div>
          {/* Archive badge */}
          <div style={{ flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, paddingLeft: 16, borderLeft: '1px solid rgba(184,145,42,0.18)' }}>
            <span style={{ fontSize: 7, color: 'rgba(154,120,50,0.55)', letterSpacing: 2.5, fontFamily: 'monospace', fontWeight: 700 }}>ARCHIVE</span>
            <span style={{ fontSize: 13, color: 'var(--gold2)', fontFamily: 'monospace', letterSpacing: 0.5 }}>
              {String(new Date().getMonth() + 1).padStart(2,'0')}.{String(new Date().getDate()).padStart(2,'0')}
            </span>
          </div>
        </div>

        {/* Artwork recognition */}
        {candidates?.length > 0 && (
          <div className="card" style={{ padding: '18px 20px' }}>
            <SectionHead
              icon="◎"
              title={
                identification_status === 'confirmed' ? '이 작품일 가능성이 높은 후보' :
                identification_status === 'partial' ? '시각적으로 가장 유사한 후보' :
                '작품명 미확인 (유사한 후보)'
              }
              en="Artwork Candidates"
            />
            <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column' }}>
              {candidates.map((c, i) => (
                <div key={i} style={{
                  display: 'flex', gap: 16, alignItems: 'flex-start',
                  padding: '13px 0',
                  borderBottom: i < candidates.length - 1 ? '1px solid var(--line)' : 'none',
                  opacity: i === 0 ? 1 : 0.65,
                }}>
                  {/* Confidence */}
                  <div style={{ textAlign: 'center', minWidth: 50, flexShrink: 0 }}>
                    <div style={{ fontSize: i === 0 ? 16 : 13, fontWeight: 700, color: 'var(--gold2)', fontFamily: 'serif', lineHeight: 1 }}>
                      {c.confidence}%
                    </div>
                    <div style={{ fontSize: 7, color: 'var(--sub)', letterSpacing: 0.5, marginTop: 3 }}>시각적 유사도</div>
                    <div style={{ height: 2, background: `rgba(184,145,42,${(c.confidence / 100) * 0.7 + 0.1})`, borderRadius: 1, marginTop: 5 }} />
                  </div>
                  {/* Info */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ fontSize: i === 0 ? 14 : 12, fontWeight: i === 0 ? 700 : 500, color: 'var(--text)', fontFamily: "'Noto Serif KR', serif", lineHeight: 1.4, marginBottom: 3 }}>
                      {formatTitle(c.title) || '—'}
                    </p>
                    <p style={{ fontSize: 11, color: 'var(--sub)' }}>
                      {[formatArtist(c.artist), c.year].filter(Boolean).join(' · ')}
                      {c.museum && <span style={{ color: 'var(--gold)', marginLeft: 8, fontSize: 9 }}>{c.museum}</span>}
                    </p>
                    {i === 0 && c.reason && (
                      <p style={{ fontSize: 10, color: 'var(--sub)', marginTop: 6, lineHeight: 1.7, opacity: 0.85 }}>{c.reason}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <p style={{ fontSize: 9, color: 'rgba(194,166,136,0.4)', marginTop: 10, fontStyle: 'italic', textAlign: 'right', letterSpacing: 0.5 }}>
              AI 추정 결과 · 오인식이 있을 수 있습니다
            </p>
            {/* Feature 27 — correction */}
            <button onClick={() => setCorrecting(v => !v)} style={{
              marginTop: 8, background: 'transparent', border: 'none', cursor: 'pointer',
              fontSize: 10, color: 'rgba(154,120,80,0.45)', letterSpacing: 1, fontFamily: 'inherit',
              textDecoration: 'underline', textDecorationStyle: 'dotted',
            }}>
              {correcting ? '취소' : '다른 작품인 것 같아요'}
            </button>
            {correcting && (
              <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 8 }}>
                <input value={manualTitle}  onChange={e => setManualTitle(e.target.value)}  placeholder="작품명 직접 입력"
                  style={{ background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: 2, padding: '8px 12px', fontSize: 12, color: 'var(--text)', fontFamily: 'inherit', outline: 'none' }} />
                <input value={manualArtist} onChange={e => setManualArtist(e.target.value)} placeholder="화가명 직접 입력"
                  style={{ background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: 2, padding: '8px 12px', fontSize: 12, color: 'var(--text)', fontFamily: 'inherit', outline: 'none' }} />
                <button onClick={applyCorrection} className="btn-primary" style={{ height: 36, fontSize: 12, letterSpacing: 1 }}>적용하기</button>
              </div>
            )}
          </div>
        )}

        {/* OCR — only if text found not already in info */}
        {ocr_info?.raw_text && !info.title && (
          <div className="card" style={{ padding: '14px 18px' }}>
            <p style={{ fontSize: 9, color: 'var(--gold)', fontWeight: 700, letterSpacing: 2, marginBottom: 6 }}>
              이미지 텍스트 인식
            </p>
            <p style={{ fontSize: 12, color: 'var(--sub)', lineHeight: 1.8 }}>{ocr_info.raw_text}</p>
          </div>
        )}

        {/* Figure / expression */}
        {figure?.has_person && (
          <div className="card" style={{ padding: '18px 20px' }}>
            <SectionHead
              icon={
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ verticalAlign: 'middle', marginRight: 4 }}>
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
              }
              title="인물 표정 분석"
              en="Figure Analysis"
            />
            <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[
                ['표정',   figure.expression_ko],
                ['시선',   figure.gaze],
                ['자세',   figure.posture_ko],
                ['시선 방향', figure.face_direction],
              ].filter(([, v]) => v).map(([lbl, val]) => (
                <div key={lbl} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: 8, borderBottom: '1px solid var(--line)' }}>
                  <span style={{ fontSize: 11, color: 'var(--sub)' }}>{lbl}</span>
                  <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)' }}>{val}</span>
                </div>
              ))}
              {figure.impression_ko && (
                <p style={{ fontSize: 12, color: 'var(--sub)', lineHeight: 1.8, fontStyle: 'italic', marginTop: 2 }}>
                  {figure.impression_ko}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Color palette */}
        <div className="card" style={{ padding: '18px 18px' }}>
          <SectionHead icon="⊙" title="색채 분석" en="Color Analysis" />
          <div style={{ marginTop: 12 }}>
            <PaletteBar colors={color.dominant_colors} />
          </div>
          {moodTags.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 14 }}>
              {moodTags.slice(0, 6).map((t, i) => <span key={i} className="tag">{t}</span>)}
            </div>
          )}
        </div>

        {/* Composition + Person grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          {[
            {
              icon: (
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ verticalAlign: 'middle' }}>
                  <rect x="3" y="3" width="18" height="18" rx="2"/>
                  <line x1="9" y1="3" x2="9" y2="21"/>
                  <line x1="15" y1="3" x2="15" y2="21"/>
                  <line x1="3" y1="9" x2="21" y2="9"/>
                  <line x1="3" y1="15" x2="21" y2="15"/>
                </svg>
              ),
              title: '구도와 시선',
              en: 'Composition',
              items: [
                ['위치', comp.main_subject_position || '—'],
                ['방향', comp.dominant_orientation  || '—'],
                ['여백', `${Math.round((comp.negative_space_ratio||0)*100)}%`],
                ['대칭', `${Math.round((comp.symmetry_score||0)*100)}%`],
              ]
            },
            {
              icon: (
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ verticalAlign: 'middle' }}>
                  <circle cx="12" cy="12" r="4"/>
                  <line x1="12" y1="2" x2="12" y2="4"/>
                  <line x1="12" y1="20" x2="12" y2="22"/>
                  <line x1="2" y1="12" x2="4" y2="12"/>
                  <line x1="20" y1="12" x2="22" y2="12"/>
                  <line x1="4.93" y1="4.93" x2="6.34" y2="6.34"/>
                  <line x1="17.66" y1="17.66" x2="19.07" y2="19.07"/>
                  <line x1="4.93" y1="19.07" x2="6.34" y2="17.66"/>
                  <line x1="17.66" y1="6.34" x2="19.07" y2="4.93"/>
                </svg>
              ),
              title: '색채와 밝기',
              en: 'Tone & Light',
              items: [
                ['밝기', color.brightness_label],
                ['채도', color.saturation_label],
                ['대비', color.contrast_label],
                ['어두운 영역', `${Math.round((color.dark_area_ratio||0)*100)}%`],
                ['밝은 위치', color.bright_area_position || '—'],
                ...(person.human_detected ? [['자세', person.pose || '—']] : []),
              ]
            },
          ].map(({ icon, title, en, items }) => {
            const B = 'rgba(154,120,80,0.18)', L = 12, T = 6
            return (
              <div key={title} style={{ position: 'relative', background: 'var(--card)', border: '1px solid var(--line)', borderRadius: 8, padding: '16px 14px' }}>
                {[
                  { top: T, left: T, borderTop: `1px solid ${B}`, borderLeft: `1px solid ${B}` },
                  { top: T, right: T, borderTop: `1px solid ${B}`, borderRight: `1px solid ${B}` },
                  { bottom: T, left: T, borderBottom: `1px solid ${B}`, borderLeft: `1px solid ${B}` },
                  { bottom: T, right: T, borderBottom: `1px solid ${B}`, borderRight: `1px solid ${B}` },
                ].map((s, i) => <div key={i} style={{ position:'absolute', width:L, height:L, pointerEvents:'none', ...s }} />)}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  marginBottom: 3,
                  paddingLeft: 4,
                }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', color: 'var(--gold2)' }}>{icon}</span>
                  <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text)' }}>{title}</span>
                </div>
                <p style={{
                  fontSize: 9,
                  color: 'var(--sub)',
                  fontStyle: 'italic',
                  letterSpacing: 1.5,
                  marginLeft: 26,
                  marginBottom: 10,
                }}>{en}</p>
                <GoldDivider />
                <div style={{ marginTop:12, display:'flex', flexDirection:'column', gap:8 }}>
                  {items.map(([lbl, val]) => (
                    <div key={lbl} style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                      <span style={{ fontSize:10, color:'var(--sub)' }}>{lbl}</span>
                      <span style={{ fontSize:11, fontWeight:600, color:'var(--body)' }}>{val}</span>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>

        {/* Emotion bars */}
        <div className="card" style={{ padding: '18px 18px' }}>
          <SectionHead icon="◎" title="작품 분위기" en="Emotional Tone" />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 4 }}>
            {evidence.map((e, i) => (
              <div key={i}>
                <EmotionBar label={e.emotion} score={e.score} />
                <p style={{ fontSize: 9.5, color: 'var(--sub)', paddingLeft: 80, marginTop: -4, marginBottom: 2, opacity: 0.7, lineHeight: 1.3, letterSpacing: 0.2 }}>
                  {e.reasons.join(' · ')}
                </p>
              </div>
            ))}
            {restScores.map(([lbl, sc]) => <EmotionBar key={lbl} label={lbl} score={sc} />)}
          </div>
        </div>

        {/* Similar artworks */}
        {similar?.length > 0 && (
          <div className="card" style={{ padding: '18px 20px' }}>
            <SectionHead icon="⊡" title="비슷한 명화 추천" en="Similar Masterpieces" />
            <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 0 }}>
              {similar.map((s, i) => (
                <div key={i} style={{
                  padding: '13px 0',
                  borderBottom: i < similar.length - 1 ? '1px solid var(--line)' : 'none',
                  display: 'flex', gap: 14, alignItems: 'flex-start',
                }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: 'rgba(154,120,80,0.50)', letterSpacing: 1, flexShrink: 0, marginTop: 2 }}>
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ fontSize: 13, fontWeight: 700, color: 'var(--text)', fontFamily: "'Noto Serif KR', serif", lineHeight: 1.4, marginBottom: 3 }}>
                      {s.title}
                    </p>
                    <p style={{ fontSize: 11, color: 'var(--gold)', marginBottom: 5 }}>
                      {[s.artist, s.year].filter(Boolean).join(' · ')}
                    </p>
                    {s.reason && (
                      <p style={{ fontSize: 11, color: 'var(--sub)', lineHeight: 1.7, opacity: 0.85 }}>{s.reason}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Essay — corner bracket style */}
        {essayLoading ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '22px 18px', background: 'var(--card)', border: '1px solid var(--line)', borderRadius: 8 }}>
            <div style={{ display: 'flex', gap: 6 }}>
              {[0,1,2].map(i => (
                <div key={i} style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--gold)', animation: `pulse 1.4s ${i*0.46}s infinite` }} />
              ))}
            </div>
            <p style={{ fontSize: 12, color: 'var(--sub)' }}>감상 해설을 다시 작성하고 있습니다…</p>
          </div>
        ) : essayDisplayBody.length > 0 && (
          <EssayCard title="감상 해설" en="Docent Commentary">
            <div style={{ fontSize: 13, color: 'var(--body)', lineHeight: 1.9, fontFamily: "'Noto Serif KR', serif" }}>
              {essayDisplayBody.map((p, i) => (
                <p key={i} style={{ marginBottom: i < essayDisplayBody.length - 1 ? 20 : 0 }}>
                  {p.replace(/\*\*(.*?)\*\*/g, '$1').replace(/[「『][^「』\n]*[」』]/g, m => m.slice(1, -1))}
                </p>
              ))}
            </div>
          </EssayCard>
        )}

        {/* Questions — 클릭하면 바로 아래 답변 입력 */}
        {activeEssay.questions?.length > 0 && (
          <div className="card" style={{ padding: '18px 18px' }}>
            <SectionHead icon="○" title="감상 질문" en="Reflection Questions" />
            <p style={{ fontSize: 11, color: 'var(--sub)', marginTop: 6, marginBottom: 14, lineHeight: 1.6 }}>
              질문을 눌러 나의 대답을 남겨보세요
            </p>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              {activeEssay.questions.map((q, i) => (
                <div key={i} style={{
                  paddingBottom: 14, marginBottom: 14,
                  borderBottom: i < activeEssay.questions.length - 1 ? '1px dashed rgba(184,145,42,0.15)' : 'none',
                }}>
                  {/* 질문 행 — 클릭 토글 */}
                  <div
                    onClick={() => setOpenQuestion(openQuestion === i ? null : i)}
                    style={{ display: 'flex', gap: 12, alignItems: 'flex-start', cursor: 'pointer' }}
                  >
                    <span style={{
                      fontSize: 11, fontWeight: 700, letterSpacing: 1, flexShrink: 0, marginTop: 2,
                      color: questionAnswers[i] ? 'var(--gold2)' : 'var(--gold3)',
                      minWidth: 24,
                    }}>
                      {String(i + 1).padStart(2, '0')}
                    </span>
                    <p style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.7, flex: 1, userSelect: 'none' }}>{q}</p>
                    <span style={{
                      color: 'rgba(184,145,42,0.35)', fontSize: 13, flexShrink: 0, marginTop: 2,
                      transform: openQuestion === i ? 'rotate(90deg)' : 'none',
                      transition: 'transform 0.2s',
                    }}>›</span>
                  </div>

                  {/* 이미 쓴 답변 (접혔을 때) */}
                  {openQuestion !== i && questionAnswers[i] && (
                    <div style={{
                      marginLeft: 36, marginTop: 8,
                      paddingLeft: 10, borderLeft: '2px solid rgba(184,145,42,0.22)',
                    }}>
                      <p style={{
                        fontSize: 12, color: 'var(--sub)', lineHeight: 1.8,
                        fontStyle: 'italic', fontFamily: "'Noto Serif KR', serif",
                      }}>
                        {questionAnswers[i]}
                      </p>
                    </div>
                  )}

                  {/* 열린 답변 입력창 */}
                  {openQuestion === i && (
                    <div style={{ marginLeft: 36, marginTop: 10 }}>
                      <textarea
                        autoFocus
                        value={questionAnswers[i] || ''}
                        onChange={e => setQuestionAnswers(prev => ({ ...prev, [i]: e.target.value }))}
                        placeholder="나의 생각을 적어보세요…"
                        rows={3}
                        style={{
                          width: '100%', padding: '10px 12px',
                          fontSize: 12, fontFamily: "'Noto Serif KR', serif",
                          background: 'var(--bg)', color: 'var(--text)',
                          border: '1px solid rgba(184,145,42,0.45)', borderRadius: 6,
                          resize: 'none', outline: 'none', lineHeight: 1.8,
                          boxSizing: 'border-box',
                        }}
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Comfort — triple diamond */}
        {activeEssay.comfort && (
          <div className="card" style={{ padding: '28px 24px', textAlign: 'center' }}>
            <GoldDivider triple />
            <p style={{
              fontSize: 15, color: 'var(--body)',
              fontFamily: "'Noto Serif KR', serif",
              lineHeight: 1.9, margin: '20px 8px 16px',
              fontWeight: 500,
            }}>"{activeEssay.comfort}"</p>
            <p style={{ fontSize: 9, color: 'rgba(154,120,80,0.45)', letterSpacing: 3, fontWeight: 700 }}>TODAY'S MESSAGE</p>
          </div>
        )}

        {/* 작품의 시대와 이야기 */}
        <div className="card" style={{ padding: '18px 20px' }}>
          <button onClick={handleEraToggle} style={{
            width: '100%', background: 'transparent', border: 'none', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 14, color: 'var(--gold2)', lineHeight: 1 }}>◈</span>
              <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)' }}>작품의 시대와 이야기</span>
            </div>
            <span style={{
              color: 'rgba(154,120,80,0.45)', fontSize: 13,
              transform: eraOpen ? 'rotate(90deg)' : 'none', transition: 'transform 0.2s',
            }}>›</span>
          </button>
          <p style={{ fontSize: 9, color: 'var(--gold)', fontStyle: 'italic', letterSpacing: 1.5, marginLeft: 22, marginTop: 3 }}>Story & Era</p>

          {eraOpen && (
            <div style={{ marginTop: 14 }}>
              <GoldDivider />

              {eraLoading && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '18px 0' }}>
                  <div style={{ display: 'flex', gap: 6 }}>
                    {[0,1,2].map(i => (
                      <div key={i} style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--gold)', animation: `pulse 1.4s ${i*0.46}s infinite` }} />
                    ))}
                  </div>
                  <p style={{ fontSize: 12, color: 'var(--sub)' }}>작품의 배경을 찾고 있습니다…</p>
                </div>
              )}

              {eraError && !eraLoading && (
                <div style={{ marginTop: 14, display: 'flex', gap: 10, alignItems: 'center' }}>
                  <p style={{ fontSize: 12, color: 'rgba(154,120,80,0.45)', flex: 1 }}>{eraError}</p>
                  <button onClick={fetchEra} style={{ fontSize: 11, color: 'var(--gold)', background: 'transparent', border: '1px solid rgba(154,120,80,0.25)', borderRadius: 2, padding: '4px 10px', cursor: 'pointer', fontFamily: 'inherit' }}>다시 시도</button>
                </div>
              )}

              {eraData && !eraLoading && eraData._no_era && (
                <p style={{ marginTop: 14, fontSize: 12, color: 'var(--sub)', lineHeight: 1.7, fontStyle: 'italic' }}>
                  작품 정보가 확인되지 않아 시대 배경을 제공하기 어렵습니다.<br />
                  작품명이나 화가를 직접 입력하시면 더 자세한 정보를 볼 수 있어요.
                </p>
              )}

              {eraData && !eraLoading && eraData._not_in_db && (
                <p style={{ marginTop: 14, fontSize: 12, color: 'var(--sub)', lineHeight: 1.9, fontFamily: "'Noto Serif KR', serif" }}>
                  아직 이 작품에 대한 해설이 준비되지 않았어요.<br />
                  먼저 색, 구도, 분위기에서 느껴지는 인상을 자유롭게 감상해보세요.
                </p>
              )}

              {eraData && !eraLoading && !eraData._no_era && !eraData._not_in_db && (
                <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 18 }}>

                  {/* Confidence badge + 미술 사조 — same row at the very top */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                    {eraData.confidence_label && (
                      <div style={{ display: 'inline-flex', padding: '4px 10px', borderRadius: 2, border: '1px solid rgba(154,120,80,0.25)', background: 'rgba(154,120,80,0.08)' }}>
                        <span style={{ fontSize: 9, color: 'var(--gold)', letterSpacing: 1.5, fontWeight: 700 }}>{eraData.confidence_label.toUpperCase()}</span>
                      </div>
                    )}
                    {eraData.art_movement && (
                      <div style={{ textAlign: 'right' }}>
                        <p style={{ fontSize: 8, color: 'var(--gold)', letterSpacing: 2, fontWeight: 700, marginBottom: 3 }}>미술  사조</p>
                        <p style={{ fontSize: 13, color: 'var(--gold2)', fontWeight: 700, letterSpacing: 0.3, fontFamily: "'Noto Serif KR', serif" }}>{eraData.art_movement}</p>
                      </div>
                    )}
                  </div>

                  {/* Creation period — standalone block below */}
                  {eraData.creation_period && (
                    <div>
                      <p style={{ fontSize: 9, color: 'var(--gold)', letterSpacing: 2, fontWeight: 700, marginBottom: 6 }}>제작  시기</p>
                      <p style={{ fontSize: 12, color: 'var(--text)', lineHeight: 1.8, fontFamily: "'Noto Serif KR', serif" }}>{eraData.creation_period}</p>
                    </div>
                  )}

                  {/* Historical context */}
                  {eraData.historical_context && (
                    <div style={{ borderLeft: '2px solid rgba(154,120,80,0.25)', paddingLeft: 14 }}>
                      <p style={{ fontSize: 9, color: 'var(--gold)', letterSpacing: 2, fontWeight: 700, marginBottom: 6 }}>당시 시대상</p>
                      <p style={{ fontSize: 12, color: 'var(--sub)', lineHeight: 1.9, fontFamily: "'Noto Serif KR', serif" }}>{eraData.historical_context}</p>
                    </div>
                  )}

                  {/* Artist context */}
                  {eraData.artist_context && (
                    <div style={{ borderLeft: '2px solid rgba(154,120,80,0.25)', paddingLeft: 14 }}>
                      <p style={{ fontSize: 9, color: 'var(--gold)', letterSpacing: 2, fontWeight: 700, marginBottom: 6 }}>화가의 상황</p>
                      <p style={{ fontSize: 12, color: 'var(--sub)', lineHeight: 1.9, fontFamily: "'Noto Serif KR', serif" }}>{eraData.artist_context}</p>
                    </div>
                  )}

                  {/* Visual connection — brighter emphasis box */}
                  {eraData.visual_connection && (
                    <div style={{
                      background: 'rgba(154,120,80,0.06)',
                      border: '1px solid rgba(154,120,80,0.18)',
                      borderLeft: '3px solid var(--gold3)',
                      borderRadius: 6,
                      padding: '16px 18px',
                    }}>
                      <p style={{ fontSize: 9, color: 'var(--gold3)', letterSpacing: 2, fontWeight: 700, marginBottom: 10 }}>작품과 연결해 보기</p>
                      <p style={{ fontSize: 12, color: 'var(--text)', lineHeight: 1.9, fontFamily: "'Noto Serif KR', serif" }}>
                        {renderHighlightedParagraph(eraData.visual_connection, 0)}
                      </p>
                    </div>
                  )}

                  {/* Disclaimer */}
                  <p style={{ fontSize: 9, color: 'rgba(154,120,80,0.35)', letterSpacing: 0.3, lineHeight: 1.7, textAlign: 'right', fontStyle: 'italic' }}>
                    {eraData._source === 'verified_db'
                      ? '검증된 미술사 정보 기반'
                      : 'AI 생성 내용 · 일반적으로 알려진 미술사 정보 기반 · 사실 확인 필요'}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Mood color picker */}
        <div className="card" style={{ padding: '18px 20px' }}>
          <SectionHead icon="◎" title="마음 색 고르기" en="My Mood Color" />
          <p style={{ fontSize: 11, color: 'var(--sub)', marginTop: 10, marginBottom: 14, lineHeight: 1.7 }}>
            지금 내 마음을 색으로 표현한다면?
          </p>

          {/* Tabs */}
          <div style={{ display: 'flex', gap: 6, marginBottom: 16 }}>
            {[
              { key: 'preset',  label: '기본 색' },
              { key: 'palette', label: '작품 색' },
              { key: 'custom',  label: '직접 고르기' },
            ].map(({ key, label }) => (
              <button key={key} onClick={() => setMoodColorTab(key)} style={{
                flex: 1, padding: '9px 0', borderRadius: 4, fontSize: 11,
                fontFamily: 'inherit', cursor: 'pointer', letterSpacing: 0.5,
                border: moodColorTab === key ? '1px solid rgba(194, 166, 136, 0.40)' : '1px solid var(--line)',
                background: moodColorTab === key ? 'rgba(194, 166, 136, 0.08)' : 'transparent',
                color: moodColorTab === key ? 'var(--text)' : 'var(--sub)',
                fontWeight: moodColorTab === key ? 700 : 400,
                transition: 'all 0.15s',
              }}>{label}</button>
            ))}
          </div>

          {/* Tab: Preset */}
          {moodColorTab === 'preset' && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
              {MOOD_COLORS.map((c) => {
                const on = moodColor?.hex === c.hex
                return (
                  <button key={c.hex} onClick={() => setMoodColor(on ? null : c)} style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5,
                    padding: '10px 4px', background: 'transparent',
                    border: on ? '1px solid var(--gold3)' : '1px solid transparent',
                    borderRadius: 4, cursor: 'pointer', transition: 'all 0.15s',
                  }}>
                    <div style={{
                      width: 36, height: 36, borderRadius: 4, background: c.hex,
                      boxShadow: on ? '0 0 0 2px var(--gold3)' : '0 2px 8px rgba(0,0,0,0.15)',
                      transition: 'box-shadow 0.15s',
                    }} />
                    <span style={{ fontSize: 9, color: on ? 'var(--gold2)' : 'var(--sub)', letterSpacing: 0.3, fontWeight: on ? 700 : 400 }}>{c.name}</span>
                    <span style={{ fontSize: 8, color: 'rgba(154,120,80,0.50)', letterSpacing: 0.5 }}>{c.mood}</span>
                  </button>
                )
              })}
            </div>
          )}

          {/* Tab: Palette — 기본 색과 동일한 4컬럼 그리드 형식 */}
          {moodColorTab === 'palette' && (
            paletteColors.length > 0 ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
                {paletteColors.map((c, i) => {
                  const on = moodColor?.hex === c.hex
                  return (
                    <button key={i} onClick={() => setMoodColor(on ? null : c)} style={{
                      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5,
                      padding: '10px 4px', background: 'transparent',
                      border: on ? '1px solid var(--gold3)' : '1px solid transparent',
                      borderRadius: 4, cursor: 'pointer', transition: 'all 0.15s',
                    }}>
                      <div style={{
                        width: 36, height: 36, borderRadius: 4, background: c.hex,
                        boxShadow: on ? '0 0 0 2px var(--gold3)' : '0 2px 8px rgba(0,0,0,0.15)',
                        transition: 'box-shadow 0.15s',
                      }} />
                      <span style={{ fontSize: 9, color: on ? 'var(--gold2)' : 'var(--sub)', letterSpacing: 0.3, fontWeight: on ? 700 : 400, textAlign: 'center', lineHeight: 1.3 }}>{c.name}</span>
                      <span style={{ fontSize: 8, color: 'rgba(194,166,136,0.50)', letterSpacing: 0.5 }}>작품색</span>
                    </button>
                  )
                })}
              </div>
            ) : (
              <p style={{ fontSize: 11, color: 'var(--sub)', fontStyle: 'italic' }}>작품 팔레트 색상이 없습니다</p>
            )
          )}

          {/* Tab: Custom — react-colorful 커스텀 피커 */}
          {moodColorTab === 'custom' && (() => {
            const previewHex = hslToHex(hueVal, satVal, litVal)
            const Slider = ({ label, value, min, max, unit, gradient, onChange }) => {
              const pct = ((value - min) / (max - min)) * 100
              return (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <span style={{ fontSize: 8, color: 'var(--sub)', letterSpacing: 2, fontFamily: 'monospace' }}>{label}</span>
                    <span style={{ fontSize: 9, color: 'var(--body)', fontFamily: 'monospace' }}>{value}{unit}</span>
                  </div>
                  <div style={{ position: 'relative', height: 36 }}>
                    {/* 그라디언트 바 - 세로 중앙 */}
                    <div style={{ position: 'absolute', left: 0, right: 0, top: '50%', height: 10, transform: 'translateY(-50%)', borderRadius: 5, background: gradient, border: '1px solid var(--line)' }}/>
                    {/* 핸들 */}
                    <div style={{
                      position: 'absolute', top: '50%', left: `${pct}%`,
                      transform: 'translate(-50%,-50%)', pointerEvents: 'none', zIndex: 2,
                      width: 20, height: 20, borderRadius: '50%',
                      background: '#fff', border: '1.5px solid rgba(120,90,40,0.38)',
                      boxShadow: '0 1px 6px rgba(0,0,0,0.2)',
                    }}/>
                    {/* 넓은 터치 영역 */}
                    <input type="range" min={min} max={max} value={value}
                      onChange={e => onChange(Number(e.target.value))}
                      style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: 0, cursor: 'pointer', zIndex: 3, margin: 0, touchAction: 'none' }}
                    />
                  </div>
                </div>
              )
            }
            return (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                {/* 색 미리보기 */}
                <div style={{
                  height: 56, borderRadius: 6, background: previewHex,
                  border: '1px solid var(--line)', boxShadow: '0 2px 8px rgba(0,0,0,0.07)',
                  transition: 'background 0.1s',
                }}/>

                <Slider label="HUE" value={hueVal} min={0} max={359} unit="°"
                  gradient="linear-gradient(90deg,#f00,#ff0,#0f0,#0ff,#00f,#f0f,#f00)"
                  onChange={v => { setHueVal(v); setCustomHex(hslToHex(v, satVal, litVal)) }}
                />
                <Slider label="SATURATION" value={satVal} min={0} max={100} unit="%"
                  gradient={`linear-gradient(90deg,hsl(${hueVal},0%,${litVal}%),hsl(${hueVal},100%,${litVal}%))`}
                  onChange={v => { setSatVal(v); setCustomHex(hslToHex(hueVal, v, litVal)) }}
                />
                <Slider label="LIGHTNESS" value={litVal} min={5} max={95} unit="%"
                  gradient={`linear-gradient(90deg,#111,hsl(${hueVal},${satVal}%,50%),#eee)`}
                  onChange={v => { setLitVal(v); setCustomHex(hslToHex(hueVal, satVal, v)) }}
                />

                {/* Hex 표시 */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px', background: 'var(--bg)', borderRadius: 6, border: '1px solid var(--line)' }}>
                  <div style={{ width: 34, height: 34, borderRadius: 4, flexShrink: 0, background: previewHex, border: '1px solid var(--line)' }}/>
                  <div>
                    <p style={{ fontSize: 8, color: 'var(--gold2)', fontWeight: 700, marginBottom: 2, letterSpacing: 2, fontFamily: 'monospace' }}>SELECTED</p>
                    <p style={{ fontSize: 11, color: 'var(--sub)', fontFamily: 'monospace', letterSpacing: 1.5 }}>{previewHex.toUpperCase()}</p>
                  </div>
                </div>

                {/* 이름 입력 */}
                <input type="text" placeholder="이 색에 이름을 붙여보세요"
                  value={customColorName} onChange={e => setCustomColorName(e.target.value)}
                  style={{ background: 'var(--bg)', color: 'var(--text)', border: '1px solid var(--line)', borderRadius: 4, padding: '10px 14px', fontSize: 12, fontFamily: 'inherit', outline: 'none' }}
                  onFocus={e => e.target.style.borderColor = 'var(--gold3)'}
                  onBlur={e  => e.target.style.borderColor = 'var(--line)'}
                />

                {/* 선택 버튼 */}
                <button onClick={() => {
                  const name = customColorName.trim() || '나만의 색'
                  setMoodColor({ hex: previewHex, name, mood: '' })
                  setCustomHex(previewHex)
                }} className="btn-outline" style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: previewHex, flexShrink: 0 }}/>
                  이 색 선택하기
                </button>
              </div>
            )
          })()}

          {/* Selected color preview */}
          {moodColor && (
            <div style={{
              marginTop: 18, padding: '14px 16px',
              border: '1px solid rgba(194,166,136,0.22)', borderRadius: 8,
              background: 'var(--card2)',
              display: 'flex', alignItems: 'center', gap: 14,
            }}>
              <div style={{
                width: 48, height: 48, borderRadius: 6, flexShrink: 0,
                background: moodColor.hex,
                boxShadow: '0 0 0 1.5px rgba(194,166,136,0.25), 0 4px 12px rgba(0,0,0,0.12)',
              }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)', fontFamily: "'Noto Serif KR', serif", marginBottom: 3 }}>
                  {moodColor.name}
                </p>
                {moodColor.mood && (
                  <p style={{ fontSize: 11, color: 'var(--sub)', marginBottom: 2 }}>{moodColor.mood}</p>
                )}
                <p style={{ fontSize: 9, color: 'rgba(194,166,136,0.4)', letterSpacing: 0.5 }}>
                  {moodColor.hex.toUpperCase()}
                </p>
              </div>
              <button onClick={() => setMoodColor(null)} style={{
                background: 'transparent', border: 'none', cursor: 'pointer',
                fontSize: 18, color: 'rgba(194,166,136,0.35)', padding: '4px', lineHeight: 1,
              }}>×</button>
            </div>
          )}

          {/* Mood note */}
          {moodColor && (
            <div style={{ marginTop: 14 }}>
              <textarea rows={3}
                placeholder="이 색에 오늘의 마음을 덧붙여보세요…"
                value={moodNote} onChange={e => setMoodNote(e.target.value)}
                style={{
                  background: 'var(--bg)', color: 'var(--text)',
                  border: '1px solid var(--line)', borderRadius: 8,
                  padding: '12px', fontSize: 12, fontFamily: 'inherit',
                  width: '100%', resize: 'none', outline: 'none',
                  lineHeight: 1.8, transition: 'border-color 0.2s', boxSizing: 'border-box',
                }}
                onFocus={e => e.target.style.borderColor = 'rgba(184,145,42,0.6)'}
                onBlur={e  => e.target.style.borderColor = 'var(--line)'}
              />
            </div>
          )}
        </div>

        {/* Post-emotion chips */}
        <div className="card" style={{ padding: '18px 20px' }}>
          <SectionHead icon="○" title="감상 후 나의 감정" en="After Viewing" />
          <p style={{ fontSize: 11, color: 'var(--sub)', marginTop: 10, marginBottom: 12, lineHeight: 1.7 }}>
            이 그림을 본 후 어떤 감정이 느껴지나요?
          </p>
          {!showAllPost ? (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7 }}>
              {DEFAULT_EMOTIONS.map(e => {
                const on = postEmotion.includes(e)
                return (
                  <button key={e} onClick={() => togglePost(e)} style={{ padding: '7px 14px', borderRadius: 2, fontSize: 12, fontFamily: 'inherit', cursor: 'pointer', border: on ? '1px solid rgba(184,145,42,0.65)' : '1px solid var(--line)', borderTopColor: on ? 'rgba(184,145,42,0.9)' : 'var(--line)', background: on ? 'rgba(184,145,42,0.1)' : 'var(--card)', color: on ? 'var(--gold2)' : 'var(--sub)', letterSpacing: 0.5, transition: 'all 0.15s' }}>{e}</button>
                )
              })}
              {postEmotion.filter(e => !DEFAULT_EMOTIONS.includes(e)).map(e => (
                <button key={`sel-${e}`} onClick={() => togglePost(e)} style={{ padding: '7px 14px', borderRadius: 2, fontSize: 12, fontFamily: 'inherit', cursor: 'pointer', border: '1px solid rgba(184,145,42,0.65)', borderTopColor: 'rgba(184,145,42,0.9)', background: 'rgba(184,145,42,0.1)', color: 'var(--gold2)', letterSpacing: 0.5, transition: 'all 0.15s' }}>{e}</button>
              ))}
              <button onClick={() => setShowAllPost(true)} style={{ padding: '7px 12px', borderRadius: 2, fontSize: 11, fontFamily: 'inherit', cursor: 'pointer', letterSpacing: 0.5, border: '1px dashed rgba(154,120,80,0.35)', background: 'transparent', color: 'rgba(154,120,80,0.6)' }}>더 세밀한 감정 선택 ›</button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {EMOTION_CATEGORIES.map(cat => (
                <div key={cat.label}>
                  <p style={{ fontSize: 9, color: 'var(--gold3)', fontWeight: 700, letterSpacing: 2, marginBottom: 8 }}>{cat.label}</p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7 }}>
                    {cat.emotions.map(e => {
                      const on = postEmotion.includes(e)
                      return (
                        <button key={e} onClick={() => togglePost(e)} style={{ padding: '7px 14px', borderRadius: 2, fontSize: 12, fontFamily: 'inherit', cursor: 'pointer', border: on ? '1px solid rgba(184,145,42,0.65)' : '1px solid var(--line)', borderTopColor: on ? 'rgba(184,145,42,0.9)' : 'var(--line)', background: on ? 'rgba(184,145,42,0.1)' : 'var(--card)', color: on ? 'var(--gold2)' : 'var(--sub)', letterSpacing: 0.5, transition: 'all 0.15s' }}>{e}</button>
                      )
                    })}
                  </div>
                </div>
              ))}
              <button onClick={() => setShowAllPost(false)} style={{ alignSelf: 'flex-start', padding: '5px 10px', fontSize: 10, fontFamily: 'inherit', cursor: 'pointer', letterSpacing: 0.5, border: '1px solid rgba(154,120,80,0.25)', borderRadius: 2, background: 'transparent', color: 'rgba(154,120,80,0.5)' }}>접기 ↑</button>
            </div>
          )}
        </div>

        {/* Before/after emotion comparison */}
        {preEmotion?.length > 0 && postEmotion.length > 0 && (
          <div className="card" style={{ padding: '18px 20px' }}>
            <SectionHead icon="⊞" title="감상 전후 비교" en="Emotion Journey" />
            <div style={{ marginTop: 14, display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: 12, alignItems: 'start' }}>
              <div>
                <p style={{ fontSize: 9, color: 'var(--gold)', letterSpacing: 2, fontWeight: 700, marginBottom: 10, textAlign: 'center' }}>BEFORE</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, justifyContent: 'center' }}>
                  {preEmotion.map(e => (
                    <span key={e} style={{ padding: '5px 10px', borderRadius: 2, fontSize: 11, background: 'rgba(184,145,42,0.08)', border: '1px solid rgba(184,145,42,0.2)', color: 'var(--sub)' }}>{e}</span>
                  ))}
                </div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '20px 0' }}>
                <div style={{ width: 1, height: 20, background: 'rgba(184,145,42,0.2)' }} />
                <span style={{ color: 'rgba(184,145,42,0.4)', fontSize: 14, margin: '4px 0' }}>›</span>
                <div style={{ width: 1, height: 20, background: 'rgba(184,145,42,0.2)' }} />
              </div>
              <div>
                <p style={{ fontSize: 9, color: 'var(--gold2)', letterSpacing: 2, fontWeight: 700, marginBottom: 10, textAlign: 'center' }}>AFTER</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, justifyContent: 'center' }}>
                  {postEmotion.map(e => (
                    <span key={e} style={{ padding: '5px 10px', borderRadius: 2, fontSize: 11, background: 'rgba(184,145,42,0.14)', border: '1px solid rgba(184,145,42,0.45)', color: 'var(--gold2)', fontWeight: 600 }}>{e}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Reflection input */}
        <div className="card" style={{ padding: '18px 18px' }}>
          <SectionHead icon="✎" title="나의 감상" en="My Reflection" />
          <div style={{ marginTop: 4, display: 'flex', flexDirection: 'column', gap: 10 }}>
            <textarea rows={4}
              placeholder="이 그림이 오늘의 나에게 어떻게 닿았나요…"
              value={reflection} onChange={e => setReflection(e.target.value)}
              style={{
                background: 'var(--bg)', color: 'var(--text)',
                border: '1px solid var(--line)', borderRadius: 8,
                padding: '12px', fontSize: 13, fontFamily: 'inherit',
                width: '100%', resize: 'none', outline: 'none',
                lineHeight: 1.8, transition: 'border-color 0.2s',
              }}
              onFocus={e => e.target.style.borderColor = 'var(--gold)'}
              onBlur={e  => e.target.style.borderColor = 'var(--line)'}
            />
            {/* Primary CTA — filled */}
            <button className="btn-primary" onClick={handleSave} disabled={saving}>
              {saved ? '✓  저장되었습니다' : (saving ? '저장 중...' : '감상 저장하기')}
            </button>
            {/* Secondary CTA — outline */}
            <button
              onClick={() => nav('/drawing', {
                state: {
                  thumbnail:         thumbnail     || '',
                  artworkImage:      artwork_image || '',
                  palette:           (color.dominant_colors || []).slice(0, 5).map(c => c.rgb),
                  title:             safeInfo.title  || '',
                  artist:            safeInfo.artist || '',
                  moodColor:         moodColor?.hex || 'var(--card2)',
                  moods:             moodTags.slice(0, 5),
                  existingEntryDate: savedDate || '',
                }
              })}
              className="btn-outline"
              style={{ width: '100%' }}
            >
              마음 스케치하기
            </button>
            {/* Tertiary CTA — text only */}
            <button className="btn-ghost" onClick={() => nav('/')} style={{ width: '100%', height: 38, fontSize: 12, letterSpacing: 0.5 }}>
              다른 작품 감상하기
            </button>
          </div>
        </div>

        {/* AI Docent Chat */}
        <div
          ref={chatCardRef}
          className="card"
          onClick={handleChatToggle}
          style={{ padding: '18px 20px', cursor: chatOpen ? 'default' : 'pointer' }}
        >
          <div style={{
            width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            pointerEvents: 'none',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 13, color: 'var(--gold2)' }}>◎</span>
              <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)' }}>도슨트에게 질문하기</span>
            </div>
            <span style={{ color: 'rgba(184,145,42,0.4)', fontSize: 14, transform: chatOpen ? 'rotate(90deg)' : 'none', transition: 'transform 0.2s' }}>›</span>
          </div>
          <p style={{ fontSize: 9, color: 'var(--gold)', fontStyle: 'italic', letterSpacing: 1.5, marginLeft: 22, marginTop: 3, pointerEvents: 'none' }}>AI Docent</p>

          {chatOpen && (
            <div style={{ marginTop: 14 }} onClick={e => e.stopPropagation()}>
              <GoldDivider />
              {chatLog.length === 0 && (
                <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {['이 그림이 왜 슬프게 느껴질까?', '이 화가는 어떤 삶을 살았어?', '이 색채가 주는 느낌을 더 설명해줘'].map(q => (
                    <button key={q} onClick={() => setChatMsg(q)} style={{
                      padding: '7px 12px', background: 'rgba(184,145,42,0.04)', border: '1px solid rgba(184,145,42,0.14)',
                      borderRadius: 4, fontSize: 11, color: 'var(--sub)', cursor: 'pointer', fontFamily: 'inherit',
                      textAlign: 'left', lineHeight: 1.5, transition: 'background 0.15s',
                    }}>{q}</button>
                  ))}
                </div>
              )}
              <div className="chat-scroll" style={{ maxHeight: 220, overflowY: 'auto', marginTop: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
                {chatLog.map((m, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
                    <div style={{
                      maxWidth: '82%', padding: '9px 13px', borderRadius: 8, fontSize: 12, lineHeight: 1.7,
                      background: m.role === 'user' ? 'rgba(184,145,42,0.12)' : 'var(--bg)',
                      border: '1px solid ' + (m.role === 'user' ? 'rgba(184,145,42,0.25)' : 'var(--line)'),
                      color: 'var(--text)', fontFamily: m.role === 'ai' ? "'Noto Serif KR', serif" : 'inherit',
                    }}>{m.text}</div>
                  </div>
                ))}
                {chatLoading && <div style={{ fontSize: 11, color: 'var(--sub)', fontStyle: 'italic' }}>도슨트가 답변 중입니다…</div>}
                <div ref={chatEndRef} />
              </div>
              <div style={{ marginTop: 10, display: 'flex', gap: 8 }}>
                <input value={chatMsg} onChange={e => setChatMsg(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && sendChat()}
                  placeholder="작품에 대해 무엇이든 물어보세요"
                  style={{ flex: 1, background: 'var(--bg)', border: '1px solid var(--line)', borderRadius: 4, padding: '8px 12px', fontSize: 12, color: 'var(--text)', fontFamily: 'inherit', outline: 'none' }}
                />
                <button onClick={sendChat} disabled={chatLoading} style={{
                  padding: '0 16px', background: 'var(--gold2)', border: '1px solid rgba(154,120,32,0.45)',
                  borderRadius: 4, color: 'var(--card)', fontSize: 12, fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit',
                }}>전송</button>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
