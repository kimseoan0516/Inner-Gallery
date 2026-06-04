import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getExhibitions, getDailyArtworkAIC } from '../api.js'

// ── 날짜 기반 인덱스 (하루 동안 동일한 항목 유지) ───────────────────────────
const dailyIndex = (len) => {
  const d = new Date()
  const ordinal = Math.floor((d - new Date(2000, 0, 1)) / 86400000)
  return ordinal % len
}

// ── 예술가 명언 (나중에 교체 가능) ──────────────────────────────────────────
const ARTIST_QUOTES = [
  { quote: "예술은 영혼을 일상의 먼지로부터 씻어준다.", artist: "파블로 피카소", en: "Pablo Picasso", years: "1881–1973" },
  { quote: "단순함은 궁극의 정교함이다.", artist: "레오나르도 다 빈치", en: "Leonardo da Vinci", years: "1452–1519" },
  { quote: "나는 꿈을 꾸는 것이 아니라 꿈을 그린다.", artist: "빈센트 반 고흐", en: "Vincent van Gogh", years: "1853–1890" },
  { quote: "예술은 무엇보다 영혼의 상태이다.", artist: "마르크 샤갈", en: "Marc Chagall", years: "1887–1985" },
  { quote: "창의성은 용기를 필요로 한다.", artist: "앙리 마티스", en: "Henri Matisse", years: "1869–1954" },
  { quote: "예술은 보이는 것을 재현하는 것이 아니라 보이게 만드는 것이다.", artist: "파울 클레", en: "Paul Klee", years: "1879–1940" },
  { quote: "색채는 영혼에 직접 영향을 미치는 힘이다.", artist: "바실리 칸딘스키", en: "Wassily Kandinsky", years: "1866–1944" },
  { quote: "나는 자연을 모방하지 않는다. 자연과 함께 작업한다.", artist: "파블로 피카소", en: "Pablo Picasso", years: "1881–1973" },
  { quote: "아름다움은 보는 사람의 눈 속에 있다.", artist: "오귀스트 로댕", en: "Auguste Rodin", years: "1840–1917" },
  { quote: "예술가는 감수성이 뛰어난 사람이 아니라 표현력이 뛰어난 사람이다.", artist: "에바 헤세", en: "Eva Hesse", years: "1936–1970" },
  { quote: "그림은 시처럼 침묵의 시이고, 시는 그림처럼 말하는 그림이다.", artist: "레오나르도 다 빈치", en: "Leonardo da Vinci", years: "1452–1519" },
  { quote: "예술의 목적은 세상을 아름답게 보이게 하는 것이 아니라 더 명확하게 보이게 하는 것이다.", artist: "존 러스킨", en: "John Ruskin", years: "1819–1900" },
  { quote: "나는 보는 것이 아니라 느끼는 것을 그린다.", artist: "폴 세잔", en: "Paul Cézanne", years: "1839–1906" },
  { quote: "진정한 예술가는 결코 배우는 것을 멈추지 않는다.", artist: "렘브란트", en: "Rembrandt", years: "1606–1669" },
  { quote: "그림은 내 일기장이다.", artist: "프리다 칼로", en: "Frida Kahlo", years: "1907–1954" },
  { quote: "나는 완성된 것보다 만들어지는 과정이 더 아름답다고 생각한다.", artist: "앤디 워홀", en: "Andy Warhol", years: "1928–1987" },
  { quote: "색채는 나의 하루 종일의 집착이자 기쁨이며 고통이다.", artist: "클로드 모네", en: "Claude Monet", years: "1840–1926" },
  { quote: "그림을 그릴 때 나는 자신을 잊는다.", artist: "구스타프 클림트", en: "Gustav Klimt", years: "1862–1918" },
  { quote: "예술은 삶이 부족한 곳을 채운다.", artist: "살바도르 달리", en: "Salvador Dalí", years: "1904–1989" },
  { quote: "모든 아이는 예술가다. 문제는 어떻게 어른이 되어서도 예술가로 남느냐이다.", artist: "파블로 피카소", en: "Pablo Picasso", years: "1881–1973" },
]

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
      <div style={{ height: 260, background: 'var(--card)', opacity: 0.6 }} />
      <div style={{ padding: '18px 20px 22px', background: 'var(--card)', display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div style={{ height: 13, width: '60%', background: 'var(--line)', borderRadius: 4 }} />
        <div style={{ height: 10, width: '38%', background: 'var(--line)', borderRadius: 4, opacity: 0.6 }} />
        <div style={{ height: 52, background: 'var(--line)', borderRadius: 6, marginTop: 4, opacity: 0.35 }} />
      </div>
    </div>
  )
}

function DailyArtworkSection() {
  const [art, setArt] = useState(null)
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(false)
  const [imgLoaded, setImgLoaded] = useState(false)

  useEffect(() => {
    getDailyArtworkAIC()
      .then(res => setArt(res))
      .catch(() => setArt({ fallback: true }))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <ArtworkSkeleton />

  if (!art || art.fallback) {
    return (
      <div style={{
        padding: '40px 20px', textAlign: 'center', borderRadius: 12,
        background: 'var(--card)', border: '1px solid var(--line)',
      }}>
        <p style={{ fontSize: 26, opacity: 0.1, color: '#C9A84C', margin: '0 0 14px', fontFamily: 'serif' }}>◇</p>
        <p style={{ fontSize: 12, color: 'var(--sub)', lineHeight: 2 }}>
          오늘의 작품을 불러오지 못했습니다<br />
          <span style={{ fontSize: 10, color: 'rgba(122,80,48,0.4)' }}>잠시 후 새로고침해주세요</span>
        </p>
      </div>
    )
  }

  return (
    <div style={{ borderRadius: 12, overflow: 'hidden', border: '1px solid var(--line)', background: 'var(--card)' }}>
      {/* 이미지 */}
      <div style={{ position: 'relative', background: '#0f0d0a', minHeight: imgLoaded ? 0 : 240 }}>
        {!imgLoaded && (
          <div style={{ height: 240, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ fontSize: 28, opacity: 0.08, color: '#C9A84C', fontFamily: 'serif' }}>◇</span>
          </div>
        )}
        <img
          src={art.image_url}
          alt={art.title}
          onLoad={() => setImgLoaded(true)}
          onError={() => setImgLoaded(true)}
          style={{ width: '100%', display: imgLoaded ? 'block' : 'none', maxHeight: 320, objectFit: 'cover' }}
        />
        {imgLoaded && (
          <>
            <div style={{
              position: 'absolute', bottom: 0, left: 0, right: 0, height: '60%',
              background: 'linear-gradient(to top, rgba(8,6,3,0.93) 0%, rgba(8,6,3,0.3) 65%, transparent 100%)',
              pointerEvents: 'none',
            }} />
            <div style={{ position: 'absolute', bottom: 18, left: 20, right: 20 }}>
              <p style={{
                margin: '0 0 5px', fontSize: 17, fontWeight: 700,
                color: '#fff', fontFamily: "'Noto Serif KR', serif",
                lineHeight: 1.35, letterSpacing: 0.2,
                textShadow: '0 2px 12px rgba(0,0,0,0.6)',
              }}>{art.title}</p>
              <p style={{ margin: 0, fontSize: 11, color: 'rgba(255,255,255,0.68)', letterSpacing: 0.3 }}>
                {art.artist}
              </p>
            </div>
          </>
        )}
      </div>

      {/* 하단 */}
      <div style={{ padding: '16px 20px 20px' }}>
        {/* 날짜·재료 칩 */}
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
          {art.date && (
            <span style={{
              fontSize: 10, color: 'rgba(140,105,42,0.85)',
              padding: '3px 8px', borderRadius: 4,
              background: 'rgba(184,145,42,0.08)', border: '1px solid rgba(184,145,42,0.14)',
            }}>{art.date}</span>
          )}
          {art.medium && (
            <span style={{
              fontSize: 10, color: 'var(--sub)', padding: '3px 8px', borderRadius: 4,
              background: 'rgba(0,0,0,0.04)', border: '1px solid var(--line)',
              maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            }}>{art.medium}</span>
          )}
        </div>

        {/* 오늘의 질문 */}
        {art.question && (
          <div style={{
            padding: '13px 16px', borderRadius: 8, marginBottom: 14,
            background: 'rgba(184,145,42,0.04)',
            borderLeft: '2px solid rgba(184,145,42,0.35)',
            border: '1px solid rgba(184,145,42,0.12)',
          }}>
            <p style={{ margin: '0 0 4px', fontSize: 9, color: 'var(--gold)', letterSpacing: 2.5, fontWeight: 700 }}>
              오늘의 질문
            </p>
            <p style={{ margin: 0, fontSize: 13, color: 'var(--text)', lineHeight: 1.75, fontFamily: "'Noto Serif KR', serif" }}>
              {art.question}
            </p>
          </div>
        )}

        {/* 작품 설명 */}
        {art.description && (
          <div style={{ marginBottom: 14 }}>
            <div style={{
              fontSize: 11, color: 'var(--sub)', lineHeight: 1.85,
              overflow: expanded ? 'visible' : 'hidden',
              display: expanded ? 'block' : '-webkit-box',
              WebkitLineClamp: 3, WebkitBoxOrient: 'vertical',
            }}
              dangerouslySetInnerHTML={{ __html: art.description }}
            />
            <button onClick={() => setExpanded(v => !v)} style={{
              background: 'none', border: 'none', padding: '4px 0 0',
              fontSize: 10, color: 'rgba(184,145,42,0.65)', cursor: 'pointer',
            }}>
              {expanded ? '접기 ↑' : '더 보기 ›'}
            </button>
          </div>
        )}

        <button
          onClick={() => window.open(art.artic_url, '_blank', 'noopener,noreferrer')}
          style={{
            width: '100%', padding: '10px 0', background: 'transparent',
            border: '1px solid rgba(184,145,42,0.18)', borderRadius: 6,
            fontSize: 11, color: 'rgba(140,105,42,0.7)', cursor: 'pointer',
            letterSpacing: 0.8, transition: 'all 0.15s',
          }}
          onMouseEnter={e => { e.currentTarget.style.background = 'rgba(184,145,42,0.05)'; e.currentTarget.style.borderColor = 'rgba(184,145,42,0.38)' }}
          onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.borderColor = 'rgba(184,145,42,0.18)' }}
        >
          Art Institute of Chicago에서 보기 ›
        </button>
      </div>
    </div>
  )
}

// ── EXHIBITION PICK ───────────────────────────────────────────────────────────

const SOURCE_STYLE = {
  '국립현대미술관': { color: '#3C508C', dot: '#4A5FA8' },
  '예술의전당':     { color: '#7A3264', dot: '#963C7A' },
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
          ? <img src={item.thumbnail} alt={item.title} onError={() => setImgErr(true)}
              style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
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
  const quote = ARTIST_QUOTES[dailyIndex(ARTIST_QUOTES.length)]

  return (
    <div style={{
      borderRadius: 12, overflow: 'hidden',
      background: 'var(--card)', border: '1px solid var(--line)',
      padding: '36px 28px 32px',
      textAlign: 'center',
      position: 'relative',
    }}>
      {/* 장식 코너 */}
      {[
        { top: 12, left: 12, borderTop: '1px solid rgba(184,145,42,0.2)', borderLeft: '1px solid rgba(184,145,42,0.2)' },
        { top: 12, right: 12, borderTop: '1px solid rgba(184,145,42,0.2)', borderRight: '1px solid rgba(184,145,42,0.2)' },
        { bottom: 12, left: 12, borderBottom: '1px solid rgba(184,145,42,0.2)', borderLeft: '1px solid rgba(184,145,42,0.2)' },
        { bottom: 12, right: 12, borderBottom: '1px solid rgba(184,145,42,0.2)', borderRight: '1px solid rgba(184,145,42,0.2)' },
      ].map((s, i) => (
        <div key={i} style={{ position: 'absolute', width: 18, height: 18, pointerEvents: 'none', ...s }} />
      ))}

      {/* 여는 따옴표 */}
      <p style={{
        fontSize: 72, color: 'rgba(184,145,42,0.12)', fontFamily: 'Georgia, "Times New Roman", serif',
        lineHeight: 0.7, margin: '0 0 22px', userSelect: 'none', letterSpacing: -4,
      }}>
        "
      </p>

      {/* 명언 텍스트 */}
      <p style={{
        fontSize: 15, color: 'var(--text)',
        fontFamily: "'Noto Serif KR', serif",
        lineHeight: 2, letterSpacing: 0.4,
        margin: '0 0 28px',
        wordBreak: 'keep-all',
      }}>
        {quote.quote}
      </p>

      {/* 구분선 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 14, marginBottom: 18 }}>
        <div style={{ height: 1, width: 36, background: 'rgba(184,145,42,0.18)' }} />
        <span style={{ fontSize: 8, color: 'rgba(184,145,42,0.4)', letterSpacing: 3, fontFamily: 'monospace' }}>◆</span>
        <div style={{ height: 1, width: 36, background: 'rgba(184,145,42,0.18)' }} />
      </div>

      {/* 예술가 이름 */}
      <p style={{
        margin: '0 0 4px', fontSize: 13, fontWeight: 700,
        color: 'var(--gold2)', fontFamily: "'Noto Serif KR', serif", letterSpacing: 0.8,
      }}>
        {quote.artist}
      </p>
      <p style={{ margin: 0, fontSize: 10, color: 'var(--sub)', letterSpacing: 1, fontFamily: 'monospace' }}>
        {quote.en}  {quote.years && `· ${quote.years}`}
      </p>
    </div>
  )
}

// ── 메인 페이지 ───────────────────────────────────────────────────────────────

export default function Routine() {
  const nav = useNavigate()
  const [exhibitions, setExhibitions] = useState([])
  const [exLoading, setExLoading] = useState(true)
  const [exFallback, setExFallback] = useState(false)

  useEffect(() => {
    getExhibitions()
      .then(res => { setExhibitions(res.items || []); setExFallback(res.fallback || false) })
      .catch(() => setExFallback(true))
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
          <SectionLabel en="EXHIBITION PICK" ko="오늘의 전시 산책" sub="국립현대미술관 · 예술의전당" />
          {exLoading ? (
            <ExhibitionSkeleton />
          ) : (exFallback || exhibitions.length === 0) ? (
            <ExhibitionFallback />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {exhibitions.map((item, i) => (
                <ExhibitionCard
                  key={i}
                  item={item}
                  onClick={() => item.url && window.open(item.url, '_blank', 'noopener,noreferrer')}
                />
              ))}
            </div>
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
