import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getDailyArtwork } from '../api.js'
import GoldDivider from '../components/GoldDivider.jsx'

const COURSES = [
  {
    num: '01', key: 'sleep',
    title: '잠들기 전 3분 감상',  en: 'Before Sleep',
    desc: '차분한 작품 한 점과 조용한 질문 하나',
    duration: '3 min', mode: 'short',
    hint: '힐링',
  },
  {
    num: '02', key: 'mind',
    title: '마음 정리 감상',  en: 'Clear My Mind',
    desc: '지금 감정을 선택하고 작품으로 감상하기',
    duration: '5 min', mode: 'healing',
    hint: '힐링',
  },
  {
    num: '03', key: 'daily',
    title: '오늘의 명화',  en: 'Daily Masterpiece',
    desc: 'AI가 오늘 날짜에 어울리는 작품을 추천합니다',
    duration: '자유', mode: 'docent',
    hint: '도슨트',
    isDaily: true,
  },
  {
    num: '04', key: 'color',
    title: '색으로 보는 하루',  en: 'Color of Today',
    desc: '오늘의 색을 선택하고 작품 속 색채를 느껴보기',
    duration: '5 min', mode: 'analysis',
    hint: '분석',
  },
  {
    num: '05', key: 'comfort',
    title: '위로의 명화 코스',  en: 'Art of Comfort',
    desc: '따뜻한 분위기의 작품으로 마음을 다독이기',
    duration: '7 min', mode: 'healing',
    hint: '힐링',
  },
  {
    num: '06', key: 'night',
    title: '고요한 밤의 미술관',  en: 'Night Gallery',
    desc: '어두운 색감의 명화로 깊은 밤을 함께하기',
    duration: '5 min', mode: 'short',
    hint: '짧게',
  },
]

function CourseCard({ course, onClick, dailyArt }) {
  return (
    <div
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: 18,
        padding: '18px 4px',
        borderBottom: '1px solid var(--line)',
        cursor: 'pointer', transition: 'opacity 0.15s',
      }}
      onMouseEnter={e => e.currentTarget.style.opacity = '0.7'}
      onMouseLeave={e => e.currentTarget.style.opacity = '1'}
    >
      <span style={{ fontSize: 10, fontWeight: 700, color: 'rgba(184,145,42,0.5)', letterSpacing: 1.5, flexShrink: 0, minWidth: 22, fontFamily: 'serif' }}>
        {course.num}
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text)', letterSpacing: 0.4, marginBottom: 4, fontFamily: "'Noto Serif KR', serif" }}>
          {course.title}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 5 }}>
          <span style={{ fontSize: 9, color: 'var(--gold)', fontStyle: 'italic', letterSpacing: 1.5 }}>{course.en}</span>
          <span style={{ fontSize: 9, color: 'rgba(184,145,42,0.3)' }}>·</span>
          <span style={{ fontSize: 9, color: 'var(--sub)', letterSpacing: 1 }}>{course.duration}</span>
        </div>
        <div style={{ fontSize: 11, color: 'var(--sub)', lineHeight: 1.6 }}>{course.desc}</div>
        {course.isDaily && dailyArt?.title && (
          <div style={{ marginTop: 8, padding: '8px 10px', background: 'rgba(184,145,42,0.06)', border: '1px solid rgba(184,145,42,0.15)', borderRadius: 4 }}>
            <p style={{ fontSize: 10, color: 'var(--gold)', fontWeight: 700, marginBottom: 2 }}>오늘의 추천</p>
            <p style={{ fontSize: 12, color: 'var(--text)', fontFamily: "'Noto Serif KR', serif", fontWeight: 600 }}>{dailyArt.title}</p>
            <p style={{ fontSize: 10, color: 'var(--sub)', marginTop: 1 }}>{[dailyArt.artist, dailyArt.year].filter(Boolean).join(' · ')}</p>
            {dailyArt.description && (
              <p style={{ fontSize: 10, color: 'var(--sub)', marginTop: 4, lineHeight: 1.7, opacity: 0.85 }}>{dailyArt.description}</p>
            )}
          </div>
        )}
      </div>
      <span style={{ color: 'rgba(184,145,42,0.3)', fontSize: 15, flexShrink: 0 }}>›</span>
    </div>
  )
}

export default function Routine() {
  const nav = useNavigate()
  const [dailyArt,  setDailyArt]  = useState(null)
  const [loadingDay, setLoadingDay] = useState(true)

  useEffect(() => {
    getDailyArtwork().then(setDailyArt).catch(() => {}).finally(() => setLoadingDay(false))
  }, [])

  const goUpload = (mode, hint) => {
    nav('/upload', { state: { routineMode: mode, routineHint: hint } })
  }

  return (
    <div className="screen" style={{ background: 'var(--bg)' }}>
      <div className="nav-bar" style={{ background: 'var(--card)', borderBottom: '1px solid var(--line)' }}>
        <button className="btn-ghost" onClick={() => nav('/')}>←</button>
        <div style={{ flex: 1, textAlign: 'center' }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)', letterSpacing: 0.5 }}>감상 루틴</div>
          <div style={{ fontSize: 9, color: 'var(--gold)', fontStyle: 'italic', letterSpacing: 1.5 }}>Daily Routine</div>
        </div>
        <div style={{ width: 60 }} />
      </div>

      <div className="screen-scroll" style={{ padding: '20px 24px 52px', display: 'flex', flexDirection: 'column' }}>

        <p style={{ fontFamily: "'Noto Serif KR', serif", fontSize: 13, color: 'var(--sub)', lineHeight: 2, textAlign: 'center', margin: '8px 0 20px', letterSpacing: 0.3 }}>
          오늘 어떤 방식으로 작품을 만나고 싶으신가요?
        </p>

        <GoldDivider triple />

        <div style={{ borderTop: '1px solid var(--line)', marginTop: 20 }}>
          {COURSES.map(course => (
            <CourseCard
              key={course.key}
              course={course}
              dailyArt={course.isDaily ? dailyArt : null}
              onClick={() => goUpload(course.mode, course.hint)}
            />
          ))}
        </div>

        <p style={{ textAlign: 'center', fontSize: 9, color: 'rgba(122,80,48,0.35)', marginTop: 24, letterSpacing: 2.5, fontWeight: 700 }}>
          CURATED · 감상 코스
        </p>
      </div>
    </div>
  )
}
