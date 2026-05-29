import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useApp } from '../context/AppContext.jsx'

import { getJournal, updateJournalNote } from '../api.js'
import GoldDivider from '../components/GoldDivider.jsx'

export default function Journal() {
  const nav = useNavigate()
  const location = useLocation()
  const { setSelectedEntry } = useApp()
  const [records, setRecords] = useState([])

  useEffect(() => {
    getJournal().then(data => setRecords(data)).catch(() => {})
  }, [location.state?.refresh])

  const open = (rec) => { setSelectedEntry(rec); nav('/journal/detail') }

  const handleUpdateNote = async (date, note) => {
    setRecords(prev => prev.map(r => r.date === date ? { ...r, ticket_memo: note } : r))
    try {
      await updateJournalNote(date, note)
    } catch (e) {
      console.error(e)
      alert('저장에 실패했습니다. 백엔드(파이썬) 서버가 재시작되었는지 터미널을 확인해주세요!')
    }
  }

  return (
    <div className="screen" style={{ background: 'var(--bg)' }}>
      {/* Fixed header */}
      <div className="nav-bar" style={{ background: 'var(--card)', borderBottom: '1px solid var(--line)' }}>
        <button className="btn-ghost" onClick={() => nav('/')}>←</button>
        <div style={{ flex: 1, textAlign: 'center' }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)', letterSpacing: 0.5 }}>감상 기록</div>
          <div style={{ fontSize: 9, color: 'var(--gold)', fontStyle: 'italic', letterSpacing: 1.5 }}>Art Journal</div>
        </div>
        <div style={{ width: 60 }} />
      </div>

      <div className="screen-scroll" style={{ padding: '8px 20px 52px', display: 'flex', flexDirection: 'column', gap: 12 }}>

        <div style={{ textAlign: 'center', padding: '8px 0 4px' }}>
          <p style={{
            fontFamily: "'Noto Serif KR', serif",
            fontSize: 13, color: 'var(--sub)',
            fontStyle: 'italic', lineHeight: 1.9, letterSpacing: 0.5,
          }}>티켓을 열어 그날의 감상을 다시 만나보세요</p>
        </div>

        <div style={{ marginTop: -8, marginBottom: -4 }}>
          <GoldDivider />
        </div>



        {records.length === 0 ? (
          <div style={{ textAlign: 'center', marginTop: 60 }}>
            <div style={{ fontSize: 28, marginBottom: 16, opacity: 0.25, letterSpacing: 4, fontFamily: 'serif' }}>◇</div>
            <p style={{ color: 'var(--sub)', lineHeight: 2, fontSize: 13 }}>
              아직 저장된 감상 기록이 없습니다.<br />그림을 감상하고 첫 기록을 남겨보세요.
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 32, padding: '10px 10px' }}>
            {records.map((rec, i) => <TicketCard key={i} rec={rec} onClick={() => open(rec)} onUpdateNote={handleUpdateNote} />)}
          </div>
        )}
      </div>
    </div>
  )
}

function TicketCard({ rec, onClick, onUpdateNote }) {
  const [isEditing, setIsEditing] = useState(false)
  const [noteText, setNoteText] = useState(rec.ticket_memo || '')

  useEffect(() => {
    setNoteText(rec.ticket_memo || '')
  }, [rec.ticket_memo])
  const isSketch = rec.entry_type === 'sketch'
  const title    = isSketch
    ? (rec.sketch_title || '마음 스케치')
    : (rec.artwork_title || rec.essay_title || '(제목 미확인)')
  const artist   = isSketch ? '나의 기록' : (rec.artwork_artist || '')
  const imgSrc   = isSketch
    ? (rec.sketch_image  ? `data:image/jpeg;base64,${rec.sketch_image}` : null)
    : (rec.thumbnail     ? `data:image/jpeg;base64,${rec.thumbnail}` : null)
  const imgBg    = isSketch ? (rec.mood_color || '#333') : '#333'
  
  const dateObj  = new Date(rec.date.replace(' ', 'T'))
  const dateStr  = `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}-${String(dateObj.getDate()).padStart(2, '0')}`
  const timeStr  = `${String(dateObj.getHours()).padStart(2, '0')}:${String(dateObj.getMinutes()).padStart(2, '0')}`
  const venue    = rec.museum || 'Inner Gallery'

  const yy = dateObj.getFullYear().toString().substring(2)
  const mm = (dateObj.getMonth() + 1).toString().padStart(2, '0')
  const dd = dateObj.getDate().toString().padStart(2, '0')
  const ticketNo = `No. IG-${yy}${mm}${dd}`

  let snippet = rec.ticket_memo || '기록된 감상 메모가 없습니다.'
  if (snippet.length > 70 && !isEditing) snippet = snippet.substring(0, 70) + '...'

  return (
    <div 
      onClick={onClick}
      style={{ 
        display: 'flex', flexDirection: 'column', width: '100%', 
        cursor: 'pointer', filter: 'drop-shadow(0 12px 24px rgba(0,0,0,0.5))',
        transform: 'translateY(0)', transition: 'transform 0.2s',
      }}
      onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-4px)'}
      onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
    >
      
      {/* Top half - Image */}
      <div style={{
        position: 'relative', height: 420, background: imgBg,
        borderTopLeftRadius: 12, borderTopRightRadius: 12, overflow: 'hidden'
      }}>
        {imgSrc
          ? <img src={imgSrc} alt={title} style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
          : <div style={{ width:'100%', height:'100%', display:'flex', alignItems:'center', justifyContent:'center', fontSize:24, opacity:0.3, color:'var(--gold2)' }}>◇</div>
        }
        
        {/* Scalloped dot pattern for the ticket feel */}
        <div style={{ position: 'absolute', bottom: -6, left: 0, right: 0, height: 12, backgroundImage: 'radial-gradient(circle, #F4F1EB 4px, transparent 4px)', backgroundSize: '16px 12px', backgroundPosition: 'center bottom', zIndex: 2 }} />

        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to top, rgba(0,0,0,0.95) 0%, rgba(0,0,0,0.4) 40%, transparent 100%)' }} />
        
        <div style={{ position: 'absolute', top: 16, left: 22, right: 18, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ background: 'rgba(255,255,255,0.65)', color: '#111', fontSize: 10, padding: '4px 10px', borderRadius: 4, fontWeight: 700, letterSpacing: 0.5 }}>
            ARCHIVE
          </div>
          <div style={{ background: 'rgba(0,0,0,0.7)', color: 'white', fontSize: 10, padding: '4px 10px', borderRadius: 16, letterSpacing: 1 }}>
            {ticketNo}
          </div>
        </div>

        <div style={{ position: 'absolute', bottom: 22, left: 16, right: 16 }}>
          <h3 style={{ margin: 0, fontSize: 20, color: 'white', fontFamily: "'Georgia', 'Noto Serif KR', serif", letterSpacing: 0.5, marginBottom: 4 }}>{title}</h3>
          <p style={{ margin: 0, fontSize: 12, color: 'rgba(255,255,255,0.8)' }}>{artist}</p>
        </div>
      </div>

      {/* Seamless connection */}
      <div style={{ height: 16, background: '#F4F1EB' }} />

      {/* Bottom half - Details */}
      <div style={{
        background: '#F4F1EB', borderBottomLeftRadius: 12, borderBottomRightRadius: 12,
        padding: '6px 24px 24px', color: '#2A2522'
      }}>
        <div style={{ borderLeft: '2px solid #C4B5A5', paddingLeft: 12, marginBottom: 20 }}>
          <p style={{ fontSize: 9, color: '#887E75', letterSpacing: 1.5, marginBottom: 4, fontWeight: 600 }}>EXHIBITION</p>
          <p style={{ fontSize: 15, fontFamily: "'Georgia', 'Noto Serif KR', serif", fontWeight: 600, color: '#1A1614' }}>{title}</p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 18 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#887E75" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              <span style={{ fontSize: 9, color: '#887E75', letterSpacing: 1, fontWeight: 600 }}>DATE</span>
            </div>
            <div style={{ fontSize: 13, paddingLeft: 18, color: '#3A332E', fontWeight: 500 }}>{dateStr}</div>
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#887E75" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              <span style={{ fontSize: 9, color: '#887E75', letterSpacing: 1, fontWeight: 600 }}>TIME</span>
            </div>
            <div style={{ fontSize: 13, paddingLeft: 18, color: '#3A332E', fontWeight: 500 }}>{timeStr}</div>
          </div>
        </div>

        <div style={{ marginBottom: 18 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#887E75" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
            <span style={{ fontSize: 9, color: '#887E75', letterSpacing: 1, fontWeight: 600 }}>VENUE</span>
          </div>
          <div style={{ fontSize: 13, paddingLeft: 18, color: '#3A332E', fontWeight: 500 }}>{venue}</div>
        </div>


        
        <div style={{ height: 1, background: 'rgba(0,0,0,0.06)', marginBottom: 18 }} />

        <div style={{ marginBottom: 24 }} onClick={e => e.stopPropagation()}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#887E75" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <span style={{ fontSize: 9, color: '#887E75', letterSpacing: 1, fontWeight: 600 }}>PERSONAL NOTES</span>
          </div>
          {isEditing ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <textarea
                value={noteText}
                onChange={e => setNoteText(e.target.value)}
                autoFocus
                style={{
                  width: '100%', minHeight: 60, padding: 8, fontSize: 12,
                  fontFamily: "'Noto Serif KR', serif", color: '#3A332E',
                  background: 'rgba(255,255,255,0.5)', border: '1px solid #D4C9BD',
                  borderRadius: 4, resize: 'vertical', outline: 'none'
                }}
                placeholder="메모를 입력하세요..."
              />
              <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                <button onClick={() => { setIsEditing(false); setNoteText(rec.ticket_memo || '') }} style={{ background: 'transparent', border: '1px solid rgba(0,0,0,0.1)', borderRadius: 4, padding: '4px 10px', fontSize: 10, cursor: 'pointer', color: '#555' }}>취소</button>
                <button onClick={() => { onUpdateNote(rec.date, noteText); setIsEditing(false) }} style={{ background: '#3A332E', color: 'white', border: 'none', borderRadius: 4, padding: '4px 10px', fontSize: 10, cursor: 'pointer' }}>저장</button>
              </div>
            </div>
          ) : (
            <p 
              onClick={() => setIsEditing(true)}
              style={{ fontSize: 12, color: '#524A44', lineHeight: 1.8, fontStyle: 'italic', fontFamily: "'Noto Serif KR', serif", cursor: 'text', padding: '4px 6px', margin: '-4px -6px', borderRadius: 4, transition: 'background 0.2s', minHeight: '28px' }}
              onMouseEnter={e => e.currentTarget.style.background = 'rgba(0,0,0,0.03)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              "{snippet}"
            </p>
          )}
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <button style={{ flex: 1, background: 'transparent', border: '1px solid #D4C9BD', borderRadius: 6, padding: '10px 0', fontSize: 12, color: '#3A332E', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, cursor: 'pointer', outline: 'none' }} onClick={(e)=>{e.stopPropagation()}}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg> Like
          </button>
          <button style={{ flex: 1, background: 'transparent', border: '1px solid #D4C9BD', borderRadius: 6, padding: '10px 0', fontSize: 12, color: '#3A332E', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, cursor: 'pointer', outline: 'none' }} onClick={(e)=>{e.stopPropagation()}}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg> Share
          </button>
        </div>
      </div>
    </div>
  )
}
