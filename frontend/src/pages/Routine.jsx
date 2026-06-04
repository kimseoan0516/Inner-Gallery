import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getExhibitions, getDailyArtworkAIC } from '../api.js'

// ── 오늘의 작품 ───────────────────────────────────────────────────────────────

function ArtworkSkeleton() {
  return (
    <div style={{ borderRadius: 12, overflow: 'hidden', border: '1px solid var(--line)' }}>
      <div style={{ height: 260, background: 'var(--card)' }} />
      <div style={{ padding: '20px 20px 24px', background: 'var(--card)', display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div style={{ height: 13, width: '65%', background: 'var(--line)', borderRadius: 4 }} />
        <div style={{ height: 11, width: '42%', background: 'var(--line)', borderRadius: 4, opacity: 0.6 }} />
        <div style={{ height: 48, background: 'var(--line)', borderRadius: 6, marginTop: 6, opacity: 0.4 }} />
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
        padding: '36px 20px', textAlign: 'center', borderRadius: 12,
        background: 'var(--card)', border: '1px solid var(--line)',
      }}>
        <p style={{ fontSize: 28, opacity: 0.12, color: '#C9A84C', margin: '0 0 12px', fontFamily: 'serif' }}>◇</p>
        <p style={{ fontSize: 12, color: 'var(--sub)', lineHeight: 1.9 }}>
          작품을 불러오지 못했습니다<br />
          <span style={{ fontSize: 10, color: 'rgba(122,80,48,0.4)' }}>잠시 후 다시 시도해주세요</span>
        </p>
      </div>
    )
  }

  return (
    <div style={{ borderRadius: 12, overflow: 'hidden', border: '1px solid var(--line)' }}>
      {/* 이미지 영역 */}
      <div style={{ position: 'relative', background: '#111009', minHeight: imgLoaded ? 0 : 240 }}>
        {!imgLoaded && (
          <div style={{
            height: 240, display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <span style={{ fontSize: 32, opacity: 0.1, color: '#C9A84C', fontFamily: 'serif' }}>◇</span>
          </div>
        )}
        <img
          src={art.image_url}
          alt={art.title}
          onLoad={() => setImgLoaded(true)}
          onError={() => setImgLoaded(true)}
          style={{
            width: '100%', display: imgLoaded ? 'block' : 'none',
            maxHeight: 320, objectFit: 'cover',
          }}
        />
        {/* 하단 그라디언트 */}
        {imgLoaded && (
          <div style={{
            position: 'absolute', bottom: 0, left: 0, right: 0, height: '55%',
            background: 'linear-gradient(to top, rgba(10,8,5,0.92) 0%, rgba(10,8,5,0.4) 60%, transparent 100%)',
            pointerEvents: 'none',
          }} />
        )}
        {/* 이미지 위 제목·작가 */}
        {imgLoaded && (
          <div style={{ position: 'absolute', bottom: 18, left: 20, right: 20 }}>
            <p style={{
              margin: '0 0 4px', fontSize: 17, fontWeight: 700,
              color: '#fff', fontFamily: "'Noto Serif KR', serif",
              letterSpacing: 0.2, lineHeight: 1.35,
              textShadow: '0 2px 8px rgba(0,0,0,0.5)',
            }}>
              {art.title}
            </p>
            <p style={{ margin: 0, fontSize: 11, color: 'rgba(255,255,255,0.7)', letterSpacing: 0.3 }}>
              {art.artist}
            </p>
          </div>
        )}
      </div>

      {/* 하단 텍스트 영역 */}
      <div style={{ background: 'var(--card)', padding: '16px 20px 20px' }}>

        {/* 날짜 · 재료 칩 */}
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
          {art.date && (
            <span style={{
              fontSize: 10, color: 'rgba(140,105,42,0.85)',
              padding: '3px 8px', borderRadius: 4,
              background: 'rgba(184,145,42,0.09)',
              border: '1px solid rgba(184,145,42,0.15)',
              letterSpacing: 0.3,
            }}>{art.date}</span>
          )}
          {art.medium && (
            <span style={{
              fontSize: 10, color: 'var(--sub)',
              padding: '3px 8px', borderRadius: 4,
              background: 'rgba(0,0,0,0.04)',
              border: '1px solid var(--line)',
              maxWidth: 200,
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            }}>{art.medium}</span>
          )}
        </div>

        {/* 오늘의 질문 */}
        <div style={{
          padding: '14px 16px', borderRadius: 8, marginBottom: 14,
          background: 'rgba(184,145,42,0.04)',
          border: '1px solid rgba(184,145,42,0.14)',
          borderLeft: '3px solid rgba(184,145,42,0.4)',
        }}>
          <p style={{ margin: '0 0 5px', fontSize: 9, color: 'var(--gold)', letterSpacing: 2.5, fontWeight: 700 }}>
            오늘의 질문
          </p>
          <p style={{
            margin: 0, fontSize: 13,
            color: 'var(--text)', lineHeight: 1.75,
            fontFamily: "'Noto Serif KR', serif",
          }}>
            {art.question}
          </p>
        </div>

        {/* 작품 설명 */}
        {art.description && (
          <div style={{ marginBottom: 14 }}>
            <div style={{
              fontSize: 11, color: 'var(--sub)', lineHeight: 1.85,
              overflow: expanded ? 'visible' : 'hidden',
              display: expanded ? 'block' : '-webkit-box',
              WebkitLineClamp: expanded ? 'none' : 3,
              WebkitBoxOrient: 'vertical',
            }}
              dangerouslySetInnerHTML={{ __html: art.description }}
            />
            <button
              onClick={() => setExpanded(v => !v)}
              style={{
                background: 'none', border: 'none', padding: '5px 0 0',
                fontSize: 10, color: 'rgba(184,145,42,0.7)', cursor: 'pointer',
              }}
            >
              {expanded ? '접기 ↑' : '더 보기 ›'}
            </button>
          </div>
        )}

        {/* AIC 링크 */}
        <button
          onClick={() => window.open(art.artic_url, '_blank', 'noopener,noreferrer')}
          style={{
            width: '100%', padding: '10px 0',
            background: 'transparent',
            border: '1px solid rgba(184,145,42,0.2)',
            borderRadius: 6, fontSize: 11, color: 'rgba(140,105,42,0.75)',
            cursor: 'pointer', letterSpacing: 0.8,
            transition: 'all 0.15s',
          }}
          onMouseEnter={e => { e.currentTarget.style.background = 'rgba(184,145,42,0.05)'; e.currentTarget.style.borderColor = 'rgba(184,145,42,0.4)' }}
          onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.borderColor = 'rgba(184,145,42,0.2)' }}
        >
          Art Institute of Chicago에서 보기 ›
        </button>
      </div>
    </div>
  )
}

// ── 전시 카드 ─────────────────────────────────────────────────────────────────

const SOURCE_STYLE = {
  '국립현대미술관': { bg: 'rgba(50,70,140,0.09)', color: '#3C508C', dot: '#3C508C' },
  '예술의전당':     { bg: 'rgba(120,50,100,0.09)', color: '#7A3264', dot: '#7A3264' },
}

function ExhibitionCard({ item, onClick }) {
  const [imgErr, setImgErr] = useState(false)
  const s = SOURCE_STYLE[item.source] || { bg: 'rgba(184,145,42,0.08)', color: 'rgba(140,100,30,0.9)', dot: '#B8912A' }

  const shortPeriod = (str) => {
    if (!str) return ''
    const m = str.match(/[\d.]+\s*[~－]\s*[\d.]+/)
    return m ? m[0].replace(/\s+/g, ' ') : str.slice(0, 26)
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
      {/* 좌측 컬러 바 */}
      <div style={{ width: 3, flexShrink: 0, background: s.dot, opacity: 0.55 }} />

      {/* 썸네일 */}
      <div style={{
        width: 84, flexShrink: 0,
        background: `${s.bg}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        overflow: 'hidden',
      }}>
        {item.thumbnail && !imgErr
          ? <img
              src={item.thumbnail}
              alt={item.title}
              onError={() => setImgErr(true)}
              style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
            />
          : <span style={{ fontSize: 18, opacity: 0.2, color: s.dot, fontFamily: 'serif' }}>◇</span>
        }
      </div>

      {/* 텍스트 */}
      <div style={{
        flex: 1, padding: '13px 14px',
        minWidth: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 5,
      }}>
        {/* 출처 배지 */}
        <span style={{
          display: 'inline-block', alignSelf: 'flex-start',
          fontSize: 9, fontWeight: 700, letterSpacing: 0.5,
          padding: '2px 7px', borderRadius: 3,
          background: s.bg, color: s.color,
        }}>
          {item.source}
        </span>

        {/* 제목 */}
        <p style={{
          margin: 0, fontSize: 13, fontWeight: 700,
          color: 'var(--text)', fontFamily: "'Noto Serif KR', serif",
          letterSpacing: 0.2, lineHeight: 1.4,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          {item.title}
        </p>

        {/* 장소 */}
        {item.place && (
          <p style={{ margin: 0, fontSize: 11, color: 'var(--sub)' }}>{item.place}</p>
        )}

        {/* 기간 + 요금 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
          {item.period && (
            <span style={{ fontSize: 10, color: 'rgba(122,80,48,0.5)' }}>
              {shortPeriod(item.period)}
            </span>
          )}
          {item.fee && (
            <>
              {item.period && <span style={{ fontSize: 9, color: 'rgba(184,145,42,0.25)' }}>·</span>}
              <span style={{
                fontSize: 9, fontWeight: 700, padding: '1px 5px', borderRadius: 3,
                background: isFree(item.fee) ? 'rgba(50,120,70,0.1)' : 'rgba(184,145,42,0.08)',
                color: isFree(item.fee) ? '#3C7850' : 'rgba(140,100,30,0.8)',
              }}>
                {isFree(item.fee) ? '무료' : '유료'}
              </span>
            </>
          )}
        </div>
      </div>

      {item.url && (
        <div style={{ display: 'flex', alignItems: 'center', paddingRight: 12, color: 'rgba(184,145,42,0.25)', fontSize: 15 }}>›</div>
      )}
    </div>
  )
}

function ExhibitionSkeleton() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {[1, 2, 3].map(i => (
        <div key={i} style={{
          height: 88, borderRadius: 10,
          background: 'var(--card)', border: '1px solid var(--line)', opacity: 0.4,
        }} />
      ))}
    </div>
  )
}

function ExhibitionFallback() {
  return (
    <div style={{
      padding: '30px 20px', textAlign: 'center', borderRadius: 10,
      background: 'var(--card)', border: '1px dashed rgba(184,145,42,0.18)',
    }}>
      <p style={{ fontSize: 20, opacity: 0.15, color: '#C9A84C', margin: '0 0 10px', fontFamily: 'serif' }}>◇</p>
      <p style={{ fontSize: 12, color: 'var(--sub)', lineHeight: 1.9, margin: 0 }}>
        국립현대미술관 · 예술의전당 API 키가<br />확인되지 않습니다
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
      .then(res => {
        setExhibitions(res.items || [])
        setExFallback(res.fallback || false)
      })
      .catch(() => setExFallback(true))
      .finally(() => setExLoading(false))
  }, [])

  return (
    <div className="screen" style={{ background: 'var(--bg)' }}>

      {/* 네브바 */}
      <div className="nav-bar" style={{ background: 'var(--card)', borderBottom: '1px solid var(--line)' }}>
        <button className="btn-ghost" onClick={() => nav('/')}>←</button>
        <div style={{ flex: 1, textAlign: 'center' }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)', letterSpacing: 0.5 }}>오늘의 아트 큐레이션</div>
          <div style={{ fontSize: 9, color: 'var(--gold)', fontStyle: 'italic', letterSpacing: 1.5 }}>Daily Curation</div>
        </div>
        <div style={{ width: 60 }} />
      </div>

      <div className="screen-scroll" style={{ padding: '28px 18px 60px', display: 'flex', flexDirection: 'column', gap: 32 }}>

        {/* ── 섹션 1: 오늘의 작품 ── */}
        <section>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
            <div style={{ flex: 1, height: 1, background: 'linear-gradient(to right, transparent, rgba(184,145,42,0.18))' }} />
            <p style={{
              margin: 0, fontSize: 9, color: 'rgba(184,145,42,0.55)',
              letterSpacing: 3, fontWeight: 700, fontFamily: 'monospace', whiteSpace: 'nowrap',
            }}>
              TODAY'S ARTWORK
            </p>
            <div style={{ flex: 1, height: 1, background: 'linear-gradient(to left, transparent, rgba(184,145,42,0.18))' }} />
          </div>
          <h2 style={{
            margin: '0 0 4px', fontSize: 16, fontWeight: 700,
            color: 'var(--text)', fontFamily: "'Noto Serif KR', serif", letterSpacing: 0.2,
          }}>
            오늘의 작품
          </h2>
          <p style={{ margin: '0 0 14px', fontSize: 10, color: 'var(--sub)', letterSpacing: 0.3 }}>
            Art Institute of Chicago · 퍼블릭 도메인
          </p>
          <DailyArtworkSection />
        </section>

        {/* 구분선 */}
        <div style={{ height: 1, background: 'rgba(184,145,42,0.1)' }} />

        {/* ── 섹션 2: 오늘의 전시 ── */}
        <section>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
            <div style={{ flex: 1, height: 1, background: 'linear-gradient(to right, transparent, rgba(184,145,42,0.18))' }} />
            <p style={{
              margin: 0, fontSize: 9, color: 'rgba(184,145,42,0.55)',
              letterSpacing: 3, fontWeight: 700, fontFamily: 'monospace', whiteSpace: 'nowrap',
            }}>
              TODAY'S EXHIBITION
            </p>
            <div style={{ flex: 1, height: 1, background: 'linear-gradient(to left, transparent, rgba(184,145,42,0.18))' }} />
          </div>
          <h2 style={{
            margin: '0 0 4px', fontSize: 16, fontWeight: 700,
            color: 'var(--text)', fontFamily: "'Noto Serif KR', serif", letterSpacing: 0.2,
          }}>
            오늘 밖에서 볼 수 있는 전시
          </h2>
          <p style={{ margin: '0 0 14px', fontSize: 10, color: 'var(--sub)', letterSpacing: 0.3 }}>
            국립현대미술관 · 예술의전당
          </p>

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

        {/* 하단 워터마크 */}
        <p style={{
          textAlign: 'center', fontSize: 8,
          color: 'rgba(122,80,48,0.22)',
          letterSpacing: 3, fontWeight: 700, fontFamily: 'monospace',
        }}>
          INNER GALLERY
        </p>
      </div>
    </div>
  )
}
