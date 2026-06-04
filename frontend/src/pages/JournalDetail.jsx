import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApp } from '../context/AppContext.jsx'
import { deleteJournal } from '../api.js'
import GoldDivider from '../components/GoldDivider.jsx'

function SecLabel({ icon, title, en }) {
  return (
    <div style={{ marginBottom: 2 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
        <span style={{ fontSize: 14, color: 'var(--gold2)', lineHeight: 1 }}>{icon}</span>
        <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)' }}>{title}</span>
      </div>
      {en && <p style={{ fontSize: 10, color: 'var(--gold)', fontStyle: 'italic', letterSpacing: 1.5, marginLeft: 22, marginBottom: 6 }}>{en}</p>}
      <GoldDivider />
    </div>
  )
}

export default function JournalDetail() {
  const nav = useNavigate()
  const { selectedEntry: rec } = useApp()
  const [reportOpen, setReportOpen] = useState(false)

  if (!rec) { nav('/journal'); return null }

  const eraData = rec.era_data ? (() => { try { return JSON.parse(rec.era_data) } catch { return null } })() : null

  const isSketch = rec.entry_type === 'sketch'
  const title = isSketch
    ? (rec.sketch_title || '마음 스케치')
    : (rec.artwork_title || rec.essay_title || '(제목 미확인)')

  const dateDisp = rec.date
    ? (() => {
        const [y, m, d] = rec.date.slice(0, 10).split('-')
        return `${y}년 ${m}월 ${d}일`
      })()
    : ''
  const dateTimeDisp = rec.date
    ? (() => {
        const date = new Date(rec.date.replace(' ', 'T'))
        if (Number.isNaN(date.getTime())) return rec.date
        return date.toLocaleString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
      })()
    : ''
  const ticketNo = `IG-${(rec.date || '').slice(2, 10).replace(/-/g, '')}-${String(rec.id || 0).padStart(4, '0')}`

  const handleDelete = async () => {
    if (!window.confirm('이 기록을 삭제하시겠습니까?')) return
    await deleteJournal(rec.date)
    nav('/journal')
  }

  return (
    <div className="screen" style={{ background: 'var(--bg)' }}>
      {/* Fixed header */}
      <div className="nav-bar" style={{ background: 'var(--card)', borderBottom: '1px solid var(--line)' }}>
        <button className="btn-ghost" onClick={() => nav('/journal')}>←</button>
        <div style={{ flex: 1, textAlign: 'center' }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)', letterSpacing: 0.5 }}>
            {isSketch ? '마음 스케치 기록' : '감상 기록'}
          </div>
          <div style={{ fontSize: 9, color: 'var(--gold)', fontStyle: 'italic', letterSpacing: 1.5 }}>
            {isSketch ? 'Heart Sketch' : 'Journal Entry'}
          </div>
        </div>
        <button onClick={handleDelete} style={{
          background: 'transparent', color: '#C07070',
          border: '1px solid rgba(180,80,80,0.3)', borderRadius: 6,
          padding: '0 12px', height: 32, fontSize: 12,
          cursor: 'pointer', fontFamily: 'inherit',
        }}>삭제</button>
      </div>

      <div className="screen-scroll" style={{ padding: '20px 20px 52px', display: 'flex', flexDirection: 'column', gap: 28 }}>

        {/* ── Sketch entry layout ── */}
        {isSketch ? (
          <>
            {rec.sketch_image && (
              <div style={{
                border: '1px solid rgba(184,145,42,0.30)', borderRadius: 4,
                padding: 8, background: 'var(--card2)', boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
              }}>
                <div style={{ border: '1px solid rgba(184,145,42,0.15)', borderRadius: 2 }}>
                  <img src={`data:image/jpeg;base64,${rec.sketch_image}`} alt="마음 스케치"
                    style={{ width: '100%', display: 'block', borderRadius: 2 }} />
                </div>
              </div>
            )}

            <div style={{ textAlign: 'center' }}>
              {dateDisp && <p style={{ fontSize: 10, color: 'rgba(184,145,42,0.5)', letterSpacing: 2, marginBottom: 8 }}>{dateDisp}의 스케치</p>}
              <h1 style={{ fontSize: 20, fontWeight: 700, fontFamily: "'Noto Serif KR', serif", color: 'var(--text)', lineHeight: 1.5, letterSpacing: 1, marginBottom: 6 }}>
                {title}
              </h1>
              {(rec.artwork_title || rec.artwork_artist) && (
                <p style={{ fontSize: 11, color: 'var(--sub)' }}>
                  {[rec.artwork_title, rec.artwork_artist].filter(Boolean).join('  ·  ')} 감상 후
                </p>
              )}
            </div>



            {rec.moods?.length > 0 && (
              <div className="card" style={{ padding: '16px 18px' }}>
                <SecLabel icon="◎" title="감정 키워드" en="Emotion Tags" />
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 10 }}>
                  {rec.moods.map((m, i) => <span key={i} className="tag">{m}</span>)}
                </div>
              </div>
            )}

            {rec.sketch_note && (
              <div className="card" style={{ padding: '16px 18px' }}>
                <SecLabel icon="✎" title="메모" en="Note" />
                <div style={{ marginTop: 10, borderLeft: '2px solid rgba(184,145,42,0.4)', paddingLeft: 18 }}>
                  <p style={{ fontSize: 13, color: 'var(--sub)', lineHeight: 1.9, fontStyle: 'italic', fontFamily: "'Noto Serif KR', serif" }}>
                    "{rec.sketch_note}"
                  </p>
                </div>
              </div>
            )}
          </>
        ) : (
          /* ── Main Artwork Info (Report Style) ── */
          <div style={{ padding: '0 0 12px', background: 'var(--bg)' }}>
            {/* Subtle ticket label */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <p style={{ fontSize: 9, color: 'rgba(184,145,42,0.6)', letterSpacing: 2, fontFamily: 'monospace' }}>
                INNER GALLERY · REFLECTION
              </p>
              <p style={{ fontSize: 9, color: 'var(--sub)', letterSpacing: 1, fontFamily: 'monospace' }}>
                {ticketNo}
              </p>
            </div>
            
            {/* Thin dashed line */}
            <div style={{ borderTop: '1px dashed rgba(184,145,42,0.25)', marginBottom: 20 }} />

            {rec.thumbnail && (
              <div style={{ borderRadius: 8, overflow: 'hidden', border: '1px solid rgba(184,145,42,0.15)', marginBottom: 24, boxShadow: '0 8px 24px rgba(0,0,0,0.15)' }}>
                <img src={`data:image/jpeg;base64,${rec.thumbnail}`} alt={title}
                  style={{ width: '100%', height: 'auto', display: 'block' }} />
              </div>
            )}

            <h1 style={{ fontSize: 24, fontWeight: 700, fontFamily: "'Noto Serif KR', serif", color: 'var(--text)', lineHeight: 1.4, marginBottom: 8 }}>
              {title}
            </h1>
            
            {rec.artwork_artist && (
              <p style={{ fontSize: 13, color: 'var(--sub)', letterSpacing: 0.5, marginBottom: 16 }}>
                {rec.artwork_artist}{rec.artwork_year ? `  ·  ${rec.artwork_year}` : ''}
              </p>
            )}

            <p style={{ fontSize: 11, color: 'rgba(184,145,42,0.8)', fontFamily: 'monospace', letterSpacing: 0.5, marginBottom: 20 }}>
              {dateTimeDisp || dateDisp}
            </p>

            {rec.reflection && (
              <div style={{ borderLeft: '2px solid rgba(184,145,42,0.4)', paddingLeft: 14, marginTop: 12 }}>
                <p style={{ fontSize: 13, color: 'var(--body)', lineHeight: 1.9, fontStyle: 'italic', fontFamily: "'Noto Serif KR', serif" }}>
                  "{rec.reflection}"
                </p>
              </div>
            )}
          </div>
        )}

        {/* ── 비스케치 기록 섹션 ── */}
        {!isSketch && (
          <>
            {/* ① 감정 여정 — 항상 표시, 상세 시각화 */}
            {(rec.pre_emotions?.filter(e => e !== '건너뜀').length > 0 || rec.post_emotions?.length > 0) && (
              <div className="card" style={{ padding: '22px 20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--gold2)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, opacity: 0.85 }}>
                    <circle cx="9" cy="12" r="6" />
                    <circle cx="15" cy="12" r="6" />
                  </svg>
                  <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)', letterSpacing: 0.3 }}>감정 여정</span>
                </div>
                <p style={{ fontSize: 9, color: 'var(--sub)', fontStyle: 'italic', letterSpacing: 2, marginLeft: 20, marginBottom: 10 }}>Emotion Journey</p>
                <GoldDivider />
                <div style={{ marginTop: 18, display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: 12, alignItems: 'start' }}>
                  <div>
                    <p style={{ fontSize: 8, color: 'rgba(184,145,42,0.5)', letterSpacing: 2, fontWeight: 700, marginBottom: 10, textAlign: 'center', fontFamily: 'monospace' }}>BEFORE VIEWING</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, justifyContent: 'center' }}>
                      {(rec.pre_emotions || []).filter(e => e !== '건너뜀').map((e, i) => (
                        <span key={i} style={{ padding: '4px 10px', borderRadius: 2, fontSize: 11, background: 'rgba(100,75,50,0.08)', border: '1px solid rgba(120,90,60,0.22)', color: 'var(--sub)', letterSpacing: 0.3 }}>{e}</span>
                      ))}
                    </div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: 26 }}>
                    <div style={{ width: 1, height: 14, backgroundImage: 'repeating-linear-gradient(to bottom, rgba(184,145,42,0.45) 0px, rgba(184,145,42,0.45) 4px, transparent 4px, transparent 8px)' }} />
                    <div style={{ width: 7, height: 7, transform: 'rotate(45deg)', border: '1px solid rgba(184,145,42,0.55)', background: 'transparent', margin: '3px 0' }} />
                    <div style={{ width: 1, height: 14, backgroundImage: 'repeating-linear-gradient(to bottom, rgba(184,145,42,0.45) 0px, rgba(184,145,42,0.45) 4px, transparent 4px, transparent 8px)' }} />
                  </div>
                  <div>
                    <p style={{ fontSize: 8, color: 'rgba(184,145,42,0.7)', letterSpacing: 2, fontWeight: 700, marginBottom: 10, textAlign: 'center', fontFamily: 'monospace' }}>AFTER REFLECTION</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, justifyContent: 'center' }}>
                      {(rec.post_emotions || []).map((e, i) => (
                        <span key={i} style={{ padding: '4px 10px', borderRadius: 2, fontSize: 11, background: 'rgba(184,145,42,0.12)', border: '1px solid rgba(184,145,42,0.42)', color: 'var(--gold2)', fontWeight: 600, letterSpacing: 0.3 }}>{e}</span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ② 마음 메모 — 항상 표시 */}
            {rec.mood_note && (
              <div className="card" style={{ padding: '22px 20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--gold2)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, opacity: 0.85 }}>
                    <path d="M12 2l2.4 7.6 7.6 2.4-7.6 2.4-2.4 7.6-2.4-7.6-7.6-2.4 7.6-2.4 2.4-7.6z"/>
                  </svg>
                  <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)', letterSpacing: 0.3 }}>마음의 색</span>
                </div>
                <p style={{ fontSize: 9, color: 'var(--sub)', fontStyle: 'italic', letterSpacing: 2, marginLeft: 20, marginBottom: 10 }}>Mood Color</p>
                <GoldDivider />
                <div style={{ marginTop: 16, padding: '20px 22px', background: 'rgba(184,145,42,0.03)', borderRadius: 8, border: '1px dashed rgba(184,145,42,0.2)' }}>
                  {(rec.mood_color || rec.mood_color_name) && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
                      <div style={{ width: 42, height: 42, borderRadius: '50%', background: rec.mood_color || '#8A6F39', flexShrink: 0, boxShadow: '0 4px 12px rgba(0,0,0,0.08), inset 0 2px 6px rgba(0,0,0,0.1), 0 0 0 1px rgba(184,145,42,0.15)' }} />
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        <span style={{ fontSize: 14, color: 'var(--text)', fontWeight: 700, letterSpacing: 0.5, textTransform: 'capitalize' }}>
                          {rec.mood_color_name || '나의 마음 색'}
                        </span>
                        <span style={{ fontSize: 11, color: 'rgba(184,145,42,0.6)', letterSpacing: 1, fontFamily: 'monospace' }}>
                          {rec.mood_color ? rec.mood_color.toUpperCase() : ''}
                        </span>
                      </div>
                    </div>
                  )}
                  <p style={{ fontSize: 13, color: 'var(--sub)', lineHeight: 1.95, fontStyle: 'italic', fontFamily: "'Noto Serif KR', serif", paddingLeft: 36 }}>
                    "{rec.mood_note}"
                  </p>
                </div>
              </div>
            )}

            {/* ③ 마음 스케치 / Line of Feeling — 있을 때만 표시 */}
            {rec.sketch_image && (
              <div className="card" style={{ padding: '22px 20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--gold2)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, opacity: 0.85 }}>
                    <path d="M20.24 12.24a6 6 0 0 0-8.49-8.49L5 10.5V19h8.5z"/>
                    <line x1="16" y1="8" x2="2" y2="22"/>
                    <line x1="17.5" y1="15" x2="9" y2="15"/>
                  </svg>
                  <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)', letterSpacing: 0.3 }}>마음 스케치</span>
                </div>
                <p style={{ fontSize: 9, color: 'var(--sub)', fontStyle: 'italic', letterSpacing: 2, marginLeft: 20, marginBottom: 10 }}>Line of Feeling</p>
                <GoldDivider />
                <div style={{ marginTop: 18 }}>
                  {/* 스케치 카드 — 폴라로이드 느낌 (아이보리 테마) */}
                  <div style={{
                    background: 'var(--card2)',
                    border: '1px solid rgba(184,145,42,0.22)',
                    borderRadius: 4,
                    padding: '10px 10px 22px',
                    boxShadow: '0 4px 20px rgba(0,0,0,0.07)',
                  }}>
                    <img
                      src={`data:image/jpeg;base64,${rec.sketch_image}`}
                      alt="마음 스케치"
                      style={{ width: '100%', display: 'block', borderRadius: 2, maxHeight: 280, objectFit: 'contain' }}
                    />
                    <p style={{ fontSize: 8, color: 'rgba(184,145,42,0.40)', textAlign: 'center', marginTop: 14, letterSpacing: 0.5, fontFamily: 'monospace', fontStyle: 'italic' }}>
                      작품을 마주한 마음의 흔적
                    </p>
                  </div>
                  {rec.sketch_title && rec.sketch_title !== '마음 스케치' && (
                    <p style={{ fontSize: 13, fontWeight: 700, color: 'var(--text)', fontFamily: "'Noto Serif KR', serif", textAlign: 'center', marginTop: 16 }}>
                      {rec.sketch_title}
                    </p>
                  )}
                  {rec.sketch_note && (
                    <p style={{ fontSize: 12, color: 'var(--sub)', fontFamily: "'Noto Serif KR', serif", textAlign: 'center', marginTop: 6, fontStyle: 'italic', lineHeight: 1.7 }}>
                      "{rec.sketch_note}"
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* ④⑤ 아카이브 리포트 토글 */}
            {(rec.essay_body?.length > 0 || rec.questions?.length > 0 || rec.comfort) && (
              <button
                type="button"
                onClick={() => setReportOpen(v => !v)}
                style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: 14,
                  background: 'none', border: 'none', cursor: 'pointer', padding: '6px 0', outline: 'none',
                }}
                onMouseEnter={e => e.currentTarget.querySelector('span').style.color = 'rgba(184,145,42,0.95)'}
                onMouseLeave={e => e.currentTarget.querySelector('span').style.color = 'rgba(184,145,42,0.55)'}
              >
                <div style={{ flex: 1, height: 1, background: 'linear-gradient(to right, transparent, rgba(184,145,42,0.22))' }} />
                <span style={{
                  display: 'flex', alignItems: 'center', gap: 7,
                  fontSize: 10, color: 'rgba(184,145,42,0.55)',
                  letterSpacing: 2, fontWeight: 600, fontFamily: 'monospace',
                  whiteSpace: 'nowrap', transition: 'color 0.2s', userSelect: 'none',
                }}>
                  {reportOpen ? 'CLOSE REPORT' : 'VIEW REPORT'}
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                    style={{ transform: reportOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.25s' }}>
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </span>
                <div style={{ flex: 1, height: 1, background: 'linear-gradient(to left, transparent, rgba(184,145,42,0.22))' }} />
              </button>
            )}

            {/* ⑤ 전체 리포트 (AI 해설만, 접기/펼치기) */}
            {reportOpen && (
              <>
                {/* 감상 해설 */}
                {rec.essay_body?.length > 0 && (
                  <div className="card" style={{ padding: '24px 22px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--gold2)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, opacity: 0.85 }}>
                        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                      </svg>
                      <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)', letterSpacing: 0.3 }}>감상 해설</span>
                    </div>
                    <p style={{ fontSize: 9, color: 'var(--sub)', fontStyle: 'italic', letterSpacing: 2, marginLeft: 20, marginBottom: 10 }}>Saved Commentary</p>
                    <GoldDivider />
                    <div style={{ marginTop: 20 }}>
                      {rec.essay_body.map((p, i) => (
                        <p key={i} style={{
                          fontSize: i === 0 ? 14 : 13,
                          color: i === 0 ? 'var(--text)' : 'var(--body)',
                          lineHeight: 2,
                          fontFamily: "'Noto Serif KR', serif",
                          fontWeight: i === 0 ? 500 : 400,
                          marginBottom: i < rec.essay_body.length - 1 ? 22 : 0,
                          ...(i === 0 ? { borderLeft: '2px solid rgba(184,145,42,0.35)', paddingLeft: 14 } : {}),
                        }}>{p}</p>
                      ))}
                    </div>
                  </div>
                )}

                {/* 감상 질문 */}
                {rec.questions?.length > 0 && (
                  <div className="card" style={{ padding: '22px 20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--gold2)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, opacity: 0.85 }}>
                        <circle cx="12" cy="12" r="10"/>
                        <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>
                      </svg>
                      <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)', letterSpacing: 0.3 }}>감상 질문</span>
                    </div>
                    <p style={{ fontSize: 9, color: 'var(--sub)', fontStyle: 'italic', letterSpacing: 2, marginLeft: 20, marginBottom: 10 }}>Reflection Prompts</p>
                    <GoldDivider />
                    <div style={{ display: 'flex', flexDirection: 'column', marginTop: 14 }}>
                      {rec.questions.map((q, i) => (
                        <div key={i} style={{
                          display: 'flex', gap: 14, alignItems: 'flex-start',
                          padding: '14px 0',
                          borderBottom: i < rec.questions.length - 1 ? '1px dashed rgba(184,145,42,0.18)' : 'none',
                        }}>
                          <span style={{ fontSize: 10, fontWeight: 700, color: 'rgba(184,145,42,0.55)', letterSpacing: 1, flexShrink: 0, marginTop: 3, fontFamily: 'monospace' }}>
                            Q{String(i + 1).padStart(2, '0')}
                          </span>
                          <p style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.8, fontFamily: "'Noto Serif KR', serif" }}>{q}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 수집된 메시지 */}
                {rec.comfort && (
                  <div className="card" style={{ padding: '36px 24px', textAlign: 'center' }}>
                    <p style={{ fontSize: 8, color: 'rgba(184,145,42,0.5)', letterSpacing: 3, fontWeight: 700, marginBottom: 22, fontFamily: 'monospace' }}>COLLECTED MESSAGE</p>
                    <div style={{ margin: '0 auto', maxWidth: 280 }}>
                      <p style={{ fontSize: 22, color: 'rgba(184,145,42,0.3)', lineHeight: 0.8, marginBottom: 8, fontFamily: 'serif' }}>"</p>
                      <p style={{ fontSize: 15, color: 'var(--body)', fontFamily: "'Noto Serif KR', serif", lineHeight: 2, fontWeight: 500, margin: '0 6px 8px' }}>
                        {rec.comfort}
                      </p>
                      <p style={{ fontSize: 22, color: 'rgba(184,145,42,0.3)', lineHeight: 0.8, fontFamily: 'serif' }}>"</p>
                    </div>
                    <div style={{ marginTop: 22, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
                      <div style={{ height: 1, width: 32, background: 'rgba(184,145,42,0.22)' }} />
                      <span style={{ fontSize: 7, color: 'rgba(184,145,42,0.4)', letterSpacing: 2.5, fontFamily: 'monospace' }}>INNER GALLERY</span>
                      <div style={{ height: 1, width: 32, background: 'rgba(184,145,42,0.22)' }} />
                    </div>
                  </div>
                )}

                {/* 시대배경 — 저장된 데이터 있을 때만 표시 */}
                {eraData && !eraData._no_era && !eraData._not_in_db && !eraData._error && (
                  <div className="card" style={{ padding: '22px 20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                      <span style={{ fontSize: 14, color: 'var(--gold2)', lineHeight: 1 }}>◈</span>
                      <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)', letterSpacing: 0.3 }}>작품의 시대와 이야기</span>
                    </div>
                    <p style={{ fontSize: 9, color: 'var(--gold)', fontStyle: 'italic', letterSpacing: 1.5, marginLeft: 22, marginBottom: 10 }}>Story & Era</p>
                    <GoldDivider />
                    <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 18 }}>
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
                      {eraData.creation_period && (
                        <div>
                          <p style={{ fontSize: 9, color: 'var(--gold)', letterSpacing: 2, fontWeight: 700, marginBottom: 6 }}>제작  시기</p>
                          <p style={{ fontSize: 12, color: 'var(--text)', lineHeight: 1.8, fontFamily: "'Noto Serif KR', serif" }}>{eraData.creation_period}</p>
                        </div>
                      )}
                      {eraData.historical_context && (
                        <div style={{ borderLeft: '2px solid rgba(154,120,80,0.25)', paddingLeft: 14 }}>
                          <p style={{ fontSize: 9, color: 'var(--gold)', letterSpacing: 2, fontWeight: 700, marginBottom: 6 }}>당시 시대상</p>
                          <p style={{ fontSize: 12, color: 'var(--sub)', lineHeight: 1.9, fontFamily: "'Noto Serif KR', serif" }}>{eraData.historical_context}</p>
                        </div>
                      )}
                      {eraData.artist_context && (
                        <div style={{ borderLeft: '2px solid rgba(154,120,80,0.25)', paddingLeft: 14 }}>
                          <p style={{ fontSize: 9, color: 'var(--gold)', letterSpacing: 2, fontWeight: 700, marginBottom: 6 }}>화가의 상황</p>
                          <p style={{ fontSize: 12, color: 'var(--sub)', lineHeight: 1.9, fontFamily: "'Noto Serif KR', serif" }}>{eraData.artist_context}</p>
                        </div>
                      )}
                      {eraData.visual_connection && (
                        <div style={{ background: 'rgba(154,120,80,0.06)', border: '1px solid rgba(154,120,80,0.18)', borderLeft: '3px solid var(--gold3)', borderRadius: 6, padding: '16px 18px' }}>
                          <p style={{ fontSize: 9, color: 'var(--gold3)', letterSpacing: 2, fontWeight: 700, marginBottom: 10 }}>작품과 연결해 보기</p>
                          <p style={{ fontSize: 12, color: 'var(--text)', lineHeight: 1.9, fontFamily: "'Noto Serif KR', serif" }}>{eraData.visual_connection}</p>
                        </div>
                      )}
                      <p style={{ fontSize: 9, color: 'rgba(154,120,80,0.35)', letterSpacing: 0.3, lineHeight: 1.7, textAlign: 'right', fontStyle: 'italic' }}>
                        {eraData._source === 'verified_db' ? '검증된 미술사 정보 기반' : 'AI 생성 내용 · 일반적으로 알려진 미술사 정보 기반 · 사실 확인 필요'}
                      </p>
                    </div>
                  </div>
                )}
              </>
            )}

          </>
        )}

        <button className="btn-ghost" onClick={() => nav('/journal')} style={{ width: '100%', height: 42 }}>
          기록 목록으로
        </button>
      </div>
    </div>
  )
}
