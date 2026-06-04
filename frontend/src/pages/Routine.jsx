import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { getExhibitions, getAICExhibitions, getDailyArtworkAIC, getRandomArtworkAIC, translateText, getArtistQuote } from '../api.js'
import { saveJournal } from '../api.js'
import { useAuth } from '../context/AuthContext.jsx'
import LoginModal from '../components/LoginModal.jsx'

const _stripHtml = (html) => html ? html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim() : ''

// ── 섹션 헤더 공통 컴포넌트 ──────────────────────────────────────────────────
function SectionLabel({ en, ko, sub }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
        <div style={{ flex: 1, height: 1, background: 'linear-gradient(to right, transparent, rgba(184,145,42,0.2))' }} />
        <p style={{
          margin: 0, fontSize: 9, color: 'rgba(184,145,42,0.5)',
          letterSpacing: 3.5, fontWeight: 700, fontFamily: 'monospace', whiteSpace: 'nowrap',
        }}>
          {en}
        </p>
        <div style={{ flex: 1, height: 1, background: 'linear-gradient(to left, transparent, rgba(184,145,42,0.2))' }} />
      </div>
      <h2 style={{
        margin: '0 0 3px', fontSize: 17, fontWeight: 700,
        color: 'var(--text)', fontFamily: "'Noto Serif KR', serif", letterSpacing: 0.2,
      }}>
        {ko}
      </h2>
      {sub && <p style={{ margin: 0, fontSize: 10, color: 'var(--sub)', letterSpacing: 0.3 }}>{sub}</p>}
    </div>
  )
}

// ── DAILY MASTERPIECE ─────────────────────────────────────────────────────────

function ArtworkSkeleton() {
  return (
    <div style={{ borderRadius: 12, overflow: 'hidden', border: '1px solid var(--line)' }}>
      <div style={{ height: 280, background: 'var(--card)', opacity: 0.5 }} />
      <div style={{ padding: '18px 20px 22px', background: 'var(--card)', display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div style={{ height: 13, width: '60%', background: 'var(--line)', borderRadius: 4 }} />
        <div style={{ height: 10, width: '38%', background: 'var(--line)', borderRadius: 4, opacity: 0.6 }} />
        <div style={{ height: 52, background: 'var(--line)', borderRadius: 6, marginTop: 4, opacity: 0.35 }} />
      </div>
    </div>
  )
}

function DailyArtworkSection() {
  const { user } = useAuth()
  const [art, setArt]           = useState(null)
  const [loading, setLoading]   = useState(true)
  const [shuffling, setShuffling] = useState(false)
  const [imgLoaded, setImgLoaded] = useState(false)
  const [expanded, setExpanded] = useState(false)
  // 번역
  const [translated, setTranslated]   = useState('')
  const [translating, setTranslating] = useState(false)
  // 질문 답변
  const [qOpen, setQOpen]   = useState(false)
  const [qAnswer, setQAnswer] = useState('')
  // 저장
  const [saving, setSaving] = useState(false)
  const [saved, setSaved]   = useState(false)
  const [showLogin, setShowLogin] = useState(false)

  const load = (fetcher) => {
    setLoading(true)
    setImgLoaded(false)
    setExpanded(false)
    setTranslated('')
    setQOpen(false)
    setQAnswer('')
    setSaved(false)
    fetcher()
      .then(res => setArt(res))
      .catch(() => setArt({ fallback: true }))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load(getDailyArtworkAIC) }, [])

  const handleShuffle = () => { setShuffling(true); load(getRandomArtworkAIC); setShuffling(false) }

  const handleTranslate = async () => {
    if (!art?.description || translating) return
    setTranslating(true)
    try {
      const res = await translateText(_stripHtml(art.description))
      if (res) {
        setTranslated(res)
      } else {
        alert("번역을 불러올 수 없습니다. 서버 또는 API 키 설정을 확인해주세요.")
      }
    } catch (e) {
      alert("번역 중 오류가 발생했습니다: " + (e.response?.data?.detail || e.message))
    }
    setTranslating(false)
  }

  const handleSave = async () => {
    if (!user) { setShowLogin(true); return }
    if (!qAnswer.trim() || saving || saved) return
    setSaving(true)
    try {
      const now = new Date()
      const p = n => String(n).padStart(2, '0')
      await saveJournal({
        date: `${now.getFullYear()}-${p(now.getMonth()+1)}-${p(now.getDate())} ${p(now.getHours())}:${p(now.getMinutes())}`,
        artwork_title:  art.title,
        artwork_artist: art.artist,
        artwork_year:   art.date,
        entry_type:     'routine',
        essay_title:    '오늘의 명화 감상',
        essay_body:     [],
        questions:      [art.question],
        question_answers: JSON.stringify({ '0': qAnswer }),
        reflection:     qAnswer,
        thumbnail:      art.image_url || '',
        pre_emotions: [], post_emotions: [],
        mood_color: '', mood_color_name: '', mood_note: '',
        moods: [], dominant_colors: [],
      })
      setSaved(true)
    } catch {}
    setSaving(false)
  }

  if (loading) return <ArtworkSkeleton />

  if (!art || art.fallback) return (
    <div style={{ padding: '40px 20px', textAlign: 'center', borderRadius: 12, background: 'var(--card)', border: '1px solid var(--line)' }}>
      <p style={{ fontSize: 26, opacity: 0.1, color: '#C9A84C', margin: '0 0 14px', fontFamily: 'serif' }}>◇</p>
      <p style={{ fontSize: 12, color: 'var(--sub)', lineHeight: 2 }}>
        오늘의 작품을 불러오지 못했습니다<br />
        <span style={{ fontSize: 10, color: 'rgba(122,80,48,0.4)' }}>잠시 후 새로고침해주세요</span>
      </p>
    </div>
  )

  return (
    <>
      {showLogin && <LoginModal onSuccess={() => { setShowLogin(false); handleSave() }} onClose={() => setShowLogin(false)} />}
      <div style={{ borderRadius: 12, overflow: 'hidden', border: '1px solid var(--line)', background: 'var(--card)' }}>

        {/* 이미지 — contain으로 전체 표시 */}
        <div style={{ background: '#111009', minHeight: imgLoaded ? 0 : 240, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {!imgLoaded && <span style={{ fontSize: 28, opacity: 0.08, color: '#C9A84C', fontFamily: 'serif' }}>◇</span>}
          <img
            src={art.image_url}
            alt={art.title}
            onLoad={() => setImgLoaded(true)}
            onError={() => setImgLoaded(true)}
            style={{ width: '100%', display: imgLoaded ? 'block' : 'none', objectFit: 'contain', maxHeight: 520 }}
          />
        </div>

        {/* 하단 정보 */}
        <div style={{ padding: '16px 20px 20px', display: 'flex', flexDirection: 'column', gap: 12 }}>

          {/* 제목 · 작가 */}
          <div>
            <p style={{ margin: '0 0 4px', fontSize: 16, fontWeight: 700, color: 'var(--text)', fontFamily: "'Noto Serif KR', serif", lineHeight: 1.4 }}>{art.title}</p>
            {art.artist && <p style={{ margin: 0, fontSize: 12, color: 'var(--sub)' }}>{art.artist}</p>}
          </div>

          {/* 날짜·재료 칩 */}
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {art.date && <span style={{ fontSize: 10, color: 'rgba(140,105,42,0.85)', padding: '3px 8px', borderRadius: 4, background: 'rgba(184,145,42,0.08)', border: '1px solid rgba(184,145,42,0.14)' }}>{art.date}</span>}
            {art.medium && <span style={{ fontSize: 10, color: 'var(--sub)', padding: '3px 8px', borderRadius: 4, background: 'rgba(0,0,0,0.04)', border: '1px solid var(--line)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{art.medium}</span>}
          </div>

          {/* 오늘의 질문 — 클릭하면 답변 입력 */}
          {art.question && (
            <div style={{ borderRadius: 8, background: 'rgba(184,145,42,0.04)', border: '1px solid rgba(184,145,42,0.14)', borderLeft: '2px solid rgba(184,145,42,0.4)' }}>
              <div
                onClick={() => setQOpen(v => !v)}
                style={{ padding: '12px 16px', cursor: 'pointer' }}
              >
                <p style={{ margin: '0 0 4px', fontSize: 9, color: 'var(--gold)', letterSpacing: 2.5, fontWeight: 700 }}>오늘의 질문</p>
                <p style={{ margin: 0, fontSize: 13, color: 'var(--text)', lineHeight: 1.75, fontFamily: "'Noto Serif KR', serif" }}>{art.question}</p>
              </div>
              {qOpen && (
                <div style={{ padding: '0 16px 14px', display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <textarea
                    autoFocus
                    rows={3}
                    value={qAnswer}
                    onChange={e => setQAnswer(e.target.value)}
                    placeholder="나의 생각을 적어보세요…"
                    style={{ width: '100%', padding: '10px 12px', fontSize: 12, fontFamily: "'Noto Serif KR', serif", background: 'var(--bg)', color: 'var(--text)', border: '1px solid rgba(184,145,42,0.35)', borderRadius: 6, resize: 'none', outline: 'none', lineHeight: 1.8, boxSizing: 'border-box' }}
                  />
                  <button
                    className="btn-primary"
                    onClick={handleSave}
                    disabled={saving || saved || !qAnswer.trim()}
                    style={{
                      alignSelf: 'flex-end', padding: '7px 16px', borderRadius: 5,
                      fontSize: 11,
                      opacity: !qAnswer.trim() && !saved ? 0.5 : 1,
                    }}
                  >
                    {saved ? '✓  저장되었습니다' : (saving ? '저장 중...' : '감상 저장하기')}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* 작품 설명 (영어) */}
          {art.description && (
            <div>
              {!translated ? (
                <>
                  <div style={{ fontSize: 11, color: 'var(--sub)', lineHeight: 1.85, overflow: expanded ? 'visible' : 'hidden', display: expanded ? 'block' : '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical' }}
                    dangerouslySetInnerHTML={{ __html: art.description }}
                  />
                  <div style={{ display: 'flex', gap: 12, marginTop: 6, alignItems: 'center' }}>
                    <button onClick={() => setExpanded(v => !v)} style={{ background: 'none', border: 'none', padding: 0, fontSize: 10, color: 'rgba(184,145,42,0.65)', cursor: 'pointer' }}>
                      {expanded ? '접기 ↑' : '더 보기 ›'}
                    </button>
                    <button
                      onClick={handleTranslate}
                      disabled={translating}
                      style={{ background: 'none', border: '1px solid rgba(184,145,42,0.25)', borderRadius: 4, padding: '3px 10px', fontSize: 10, color: 'rgba(140,105,42,0.8)', cursor: translating ? 'wait' : 'pointer' }}
                    >
                      {translating ? '번역 중…' : '한국어로 번역'}
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <p style={{ fontSize: 11, color: 'var(--sub)', lineHeight: 1.9, fontFamily: "'Noto Serif KR', serif" }}>{translated}</p>
                  <button onClick={() => setTranslated('')} style={{ background: 'none', border: 'none', padding: '4px 0 0', fontSize: 10, color: 'rgba(184,145,42,0.55)', cursor: 'pointer' }}>원문 보기 ›</button>
                </>
              )}
            </div>
          )}

          {/* 버튼 행 */}
          <div style={{ display: 'flex', gap: 8, marginTop: 2 }}>
            <button
              onClick={handleShuffle}
              disabled={shuffling}
              style={{ flex: 1, padding: '10px 0', background: 'transparent', border: '1px solid var(--line)', borderRadius: 6, fontSize: 11, color: 'var(--sub)', cursor: shuffling ? 'wait' : 'pointer' }}
            >
              {shuffling ? '불러오는 중…' : '다른 작품 보기 ›'}
            </button>
            <button
              onClick={() => window.open(art.artic_url, '_blank', 'noopener,noreferrer')}
              style={{ flex: 1, padding: '10px 0', background: 'transparent', border: '1px solid rgba(184,145,42,0.22)', borderRadius: 6, fontSize: 11, color: 'rgba(140,105,42,0.75)', cursor: 'pointer' }}
            >
              AIC에서 보기 ›
            </button>
          </div>
        </div>
      </div>
    </>
  )
}

// ── EXHIBITION PICK ───────────────────────────────────────────────────────────

const SOURCE_STYLE = {
  '국립현대미술관':            { color: '#3C508C', dot: '#4A5FA8' },
  '예술의전당':                { color: '#7A3264', dot: '#963C7A' },
  'Art Institute of Chicago': { color: '#7A4020', dot: '#A05030' },
}

function ExhibitionCard({ item, onClick }) {
  const [imgErr, setImgErr] = useState(false)
  const s = SOURCE_STYLE[item.source] || { color: 'rgba(140,100,30,0.9)', dot: '#B8912A' }

  const shortPeriod = (str) => {
    if (!str) return ''
    const m = str.match(/[\d.]+\s*[~－\-]\s*[\d.]+/)
    return m ? m[0].replace(/\s+/g, ' ') : str.slice(0, 24)
  }
  const isFree = (fee) => fee && (fee === '무료' || fee.includes('무료') || fee.trim() === '0원')

  return (
    <div
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'stretch',
        background: 'var(--card)', borderRadius: 10,
        overflow: 'hidden', border: '1px solid var(--line)',
        cursor: item.url ? 'pointer' : 'default',
        transition: 'opacity 0.15s',
      }}
      onMouseEnter={e => e.currentTarget.style.opacity = '0.72'}
      onMouseLeave={e => e.currentTarget.style.opacity = '1'}
    >
      <div style={{ width: 3, flexShrink: 0, background: s.dot, opacity: 0.5 }} />
      <div style={{
        width: 82, flexShrink: 0, background: 'rgba(0,0,0,0.03)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden',
      }}>
        {item.thumbnail && !imgErr
          ? <img
              src={item.thumbnail}
              alt={item.title}
              referrerPolicy="no-referrer"
              onError={() => setImgErr(true)}
              style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
            />
          : <span style={{ fontSize: 16, opacity: 0.15, color: s.dot, fontFamily: 'serif' }}>◇</span>
        }
      </div>
      <div style={{ flex: 1, padding: '13px 14px', minWidth: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 5 }}>
        <span style={{
          alignSelf: 'flex-start', fontSize: 9, fontWeight: 700, letterSpacing: 0.5,
          padding: '2px 6px', borderRadius: 3,
          background: `${s.dot}18`, color: s.color,
        }}>{item.source}</span>
        <p style={{
          margin: 0, fontSize: 13, fontWeight: 700, color: 'var(--text)',
          fontFamily: "'Noto Serif KR', serif", letterSpacing: 0.2, lineHeight: 1.4,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>{item.title}</p>
        {item.place && <p style={{ margin: 0, fontSize: 11, color: 'var(--sub)' }}>{item.place}</p>}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {item.period && <span style={{ fontSize: 10, color: 'rgba(122,80,48,0.5)' }}>{shortPeriod(item.period)}</span>}
          {item.fee && <span style={{
            fontSize: 9, fontWeight: 700, padding: '1px 5px', borderRadius: 3,
            background: isFree(item.fee) ? 'rgba(50,120,70,0.1)' : 'rgba(184,145,42,0.08)',
            color: isFree(item.fee) ? '#3C7850' : 'rgba(140,100,30,0.8)',
          }}>{isFree(item.fee) ? '무료' : '유료'}</span>}
        </div>
      </div>
      {item.url && <div style={{ display: 'flex', alignItems: 'center', paddingRight: 12, color: 'rgba(184,145,42,0.22)', fontSize: 16 }}>›</div>}
    </div>
  )
}

function ExhibitionSkeleton() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {[1, 2, 3].map(i => (
        <div key={i} style={{ height: 88, borderRadius: 10, background: 'var(--card)', border: '1px solid var(--line)', opacity: 0.4 }} />
      ))}
    </div>
  )
}

function ExhibitionFallback() {
  return (
    <div style={{
      padding: '32px 20px', textAlign: 'center', borderRadius: 10,
      background: 'var(--card)', border: '1px dashed rgba(184,145,42,0.16)',
    }}>
      <p style={{ fontSize: 20, opacity: 0.12, color: '#C9A84C', margin: '0 0 10px', fontFamily: 'serif' }}>◇</p>
      <p style={{ fontSize: 12, color: 'var(--sub)', lineHeight: 1.9, margin: 0 }}>
        전시 정보를 불러오지 못했습니다
      </p>
    </div>
  )
}

// ── ARTIST'S WORDS ────────────────────────────────────────────────────────────

function ArtistWords() {
  const [quote, setQuote] = useState(null)
  const [loading, setLoading] = useState(true)
  const [fading, setFading] = useState(false)

  const fetchQuote = () => {
    setFading(true)
    setTimeout(() => {
      setLoading(true)
      getArtistQuote()
        .then(res => setQuote(res))
        .catch(() => setQuote(null))
        .finally(() => { setLoading(false); setFading(false) })
    }, 200)
  }

  useEffect(() => {
    getArtistQuote()
      .then(res => setQuote(res))
      .catch(() => setQuote(null))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div style={{ height: 180, borderRadius: 10, background: 'var(--card)', border: '1px solid var(--line)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ display: 'flex', gap: 5 }}>
          {[0,1,2].map(i => <div key={i} style={{ width: 5, height: 5, borderRadius: '50%', background: 'rgba(184,145,42,0.4)', animation: `pulse 1.4s ${i*0.46}s infinite` }} />)}
        </div>
      </div>
    )
  }

  if (!quote?.quote) return null

  return (
    <div style={{
      borderRadius: 10,
      background: 'var(--card)',
      border: '1px solid var(--line)',
      overflow: 'hidden',
      opacity: fading ? 0 : 1,
      transition: 'opacity 0.2s',
    }}>
      {/* 상단 골드 라인 */}
      <div style={{ height: 2, background: 'linear-gradient(to right, transparent, rgba(184,145,42,0.35), transparent)' }} />

      <div style={{ padding: '32px 28px 24px' }}>
        {/* 오픈 쿼트 — 텍스트 왼쪽 위에 작게 */}
        <div style={{ fontSize: 40, color: 'rgba(184,145,42,0.18)', fontFamily: 'Georgia, serif', lineHeight: 1, marginBottom: 8, userSelect: 'none' }}>“</div>

        {/* 명언 텍스트 */}
        <p style={{
          margin: '0 0 8px',
          fontSize: 15,
          color: '#3A332E',
          fontFamily: "'Noto Serif KR', serif",
          lineHeight: 1.95,
          letterSpacing: 0.2,
          wordBreak: 'keep-all',
        }}>
          {quote.quote}
        </p>
        
        {quote.quote_en && (
          <p style={{
            margin: '0 0 28px',
            fontSize: 13,
            color: '#8A7B66',
            fontFamily: "serif",
            fontStyle: 'italic',
            lineHeight: 1.6,
            letterSpacing: 0.5
          }}>
            {quote.quote_en}
          </p>
        )}

        {/* 하단 — 작가명 + 둥근 버튼 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <p style={{
              margin: 0,
              fontSize: 13,
              fontWeight: 700,
              color: '#8C692A',
              fontFamily: "'Noto Serif KR', serif",
              letterSpacing: 1.5,
            }}>
              — {quote.artist}
            </p>
            {quote.artist_en && (
              <p style={{ margin: '4px 0 0', fontSize: 11, fontWeight: 500, color: 'rgba(140, 105, 42, 0.7)', letterSpacing: 0.5 }}>
                ({quote.artist_en})
              </p>
            )}
          </div>

          <button
            onClick={fetchQuote}
            style={{
              background: 'linear-gradient(135deg, rgba(184,145,42,0.1), rgba(184,145,42,0.02))',
              border: '1px solid rgba(184,145,42,0.25)',
              padding: '8px 20px',
              borderRadius: 30,
              fontSize: 12,
              fontWeight: 600,
              color: 'rgba(140,105,42,0.9)',
              cursor: 'pointer',
              letterSpacing: 0.5,
              fontFamily: "'Noto Serif KR', serif",
              transition: 'all 0.25s ease',
              boxShadow: '0 2px 8px rgba(184,145,42,0.05)'
            }}
            onMouseOver={e => { 
              e.target.style.background = 'linear-gradient(135deg, rgba(184,145,42,0.15), rgba(184,145,42,0.05))'; 
              e.target.style.boxShadow = '0 4px 12px rgba(184,145,42,0.15)'; 
              e.target.style.transform = 'translateY(-1px)';
            }}
            onMouseOut={e => { 
              e.target.style.background = 'linear-gradient(135deg, rgba(184,145,42,0.1), rgba(184,145,42,0.02))';
              e.target.style.boxShadow = '0 2px 8px rgba(184,145,42,0.05)';
              e.target.style.transform = 'translateY(0)';
            }}
          >
            다른 문장 감상하기
          </button>
        </div>
      </div>
    </div>
  )
}

// ── 메인 페이지 ───────────────────────────────────────────────────────────────

export default function Routine() {
  const nav = useNavigate()
  const [exhibitions, setExhibitions] = useState([])
  const [exLoading, setExLoading] = useState(true)
  const [exFallback, setExFallback] = useState(false)
  const [exPage, setExPage] = useState(1)
  const exPerPage = 6

  useEffect(() => {
    // 한국 API + AIC 전시 병렬 fetch 후 병합
    Promise.allSettled([
      getExhibitions(),
      getAICExhibitions(),
    ]).then(([krResult, aicResult]) => {
      const krItems = krResult.status === 'fulfilled' ? (krResult.value.items || []) : []
      const aicItems = aicResult.status === 'fulfilled' ? aicResult.value : []
      const merged = [...krItems, ...aicItems]
      setExhibitions(merged)
      setExFallback(merged.length === 0)
    }).catch(() => setExFallback(true))
      .finally(() => setExLoading(false))
  }, [])

  return (
    <div className="screen" style={{ background: 'var(--bg)' }}>
      <div className="nav-bar" style={{ background: 'var(--card)', borderBottom: '1px solid var(--line)' }}>
        <button className="btn-ghost" onClick={() => nav('/')}>←</button>
        <div style={{ flex: 1, textAlign: 'center' }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)', letterSpacing: 0.5 }}>오늘의 아트 큐레이션</div>
          <div style={{ fontSize: 9, color: 'var(--gold)', fontStyle: 'italic', letterSpacing: 1.5 }}>Daily Curation</div>
        </div>
        <div style={{ width: 60 }} />
      </div>

      <div className="screen-scroll" style={{ padding: '28px 18px 64px', display: 'flex', flexDirection: 'column', gap: 36 }}>

        {/* ① DAILY MASTERPIECE */}
        <section>
          <SectionLabel en="DAILY MASTERPIECE" ko="오늘의 명화" sub="Art Institute of Chicago · 퍼블릭 도메인" />
          <DailyArtworkSection />
        </section>

        {/* ② EXHIBITION PICK */}
        <section>
          <SectionLabel en="EXHIBITION PICK" ko="오늘의 전시 산책" sub="국립현대미술관 · 예술의전당 · 국립박물관 외 27개 기관 · Art Institute of Chicago" />
          {exLoading ? (
            <ExhibitionSkeleton />
          ) : (exFallback || exhibitions.length === 0) ? (
            <ExhibitionFallback />
          ) : (
            <>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {exhibitions.slice((exPage - 1) * exPerPage, exPage * exPerPage).map((item, i) => (
                  <ExhibitionCard
                    key={i}
                    item={item}
                    onClick={() => item.url && window.open(item.url, '_blank', 'noopener,noreferrer')}
                  />
                ))}
              </div>
              
              {/* 페이지네이션 컨덕터 */}
              {exhibitions.length > exPerPage && (
                <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 16 }}>
                  <button 
                    onClick={() => setExPage(p => Math.max(1, p - 1))}
                    disabled={exPage === 1}
                    style={{ background: 'transparent', border: '1px solid var(--line)', padding: '4px 12px', borderRadius: 4, color: exPage === 1 ? 'rgba(0,0,0,0.1)' : 'var(--text)', cursor: exPage === 1 ? 'default' : 'pointer' }}
                  >
                    &lt;
                  </button>
                  <span style={{ fontSize: 12, color: 'var(--sub)', alignSelf: 'center', margin: '0 8px' }}>
                    {exPage} / {Math.ceil(exhibitions.length / exPerPage)}
                  </span>
                  <button 
                    onClick={() => setExPage(p => Math.min(Math.ceil(exhibitions.length / exPerPage), p + 1))}
                    disabled={exPage === Math.ceil(exhibitions.length / exPerPage)}
                    style={{ background: 'transparent', border: '1px solid var(--line)', padding: '4px 12px', borderRadius: 4, color: exPage === Math.ceil(exhibitions.length / exPerPage) ? 'rgba(0,0,0,0.1)' : 'var(--text)', cursor: exPage === Math.ceil(exhibitions.length / exPerPage) ? 'default' : 'pointer' }}
                  >
                    &gt;
                  </button>
                </div>
              )}
            </>
          )}
        </section>

        {/* ③ ARTIST'S WORDS */}
        <section>
          <SectionLabel en="ARTIST'S WORDS" ko="예술가의 한 문장" sub="오늘의 영감" />
          <ArtistWords />
        </section>

        <p style={{
          textAlign: 'center', fontSize: 8, margin: 0,
          color: 'rgba(122,80,48,0.2)', letterSpacing: 3.5, fontWeight: 700, fontFamily: 'monospace',
        }}>
          INNER GALLERY
        </p>
      </div>
    </div>
  )
}
