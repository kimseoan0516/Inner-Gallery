import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import GoldDivider from '../components/GoldDivider.jsx'
import { useAuth } from '../context/AuthContext.jsx'

/* ── colour constants (matches index.css bronze palette) ── */
const BRZ       = 'rgba(122,92,56,'   // deep bronze
const BRZ2      = 'rgba(154,120,80,'  // mid bronze
const BRZ3      = 'rgba(176,144,96,'  // light bronze / champagne

const IconCamera = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 8V5a2 2 0 0 1 2-2h3" />
    <path d="M21 8V5a2 2 0 0 0-2-2h-3" />
    <path d="M3 16v3a2 2 0 0 0 2 2h3" />
    <path d="M21 16v3a2 2 0 0 1-2 2h-3" />
    <circle cx="12" cy="12" r="3" />
  </svg>
)
const IconUpload = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
    <circle cx="8.5" cy="8.5" r="1.5" />
    <polyline points="21 15 16 10 5 21" />
  </svg>
)
const IconDaily = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
  </svg>
)
const IconMuseum = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M19 4H5a2 2 0 0 0-2 2v3.5a2.5 2.5 0 0 1 0 5V18a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-3.5a2.5 2.5 0 0 1 0-5V6a2 2 0 0 0-2-2z" />
    <line x1="16" y1="4" x2="16" y2="20" strokeDasharray="2 3" />
  </svg>
)

const MENU = [
  {
    num: '01', icon: <IconCamera />,
    title: '작품 촬영하기',  sub: 'Camera Scan',
    en: '전시장이나 책 속 그림 인식',
    to: '/camera',
  },
  {
    num: '02', icon: <IconUpload />,
    title: '작품 업로드',    sub: 'Image Upload',
    en: '갤러리에서 작품 선택하기',
    to: '/upload',
  },
  {
    num: '03', icon: <IconDaily />,
    title: '오늘의 감상',    sub: 'Daily Routine',
    en: '오늘의 감상 코스 시작하기',
    to: '/routine',
  },
  {
    num: '04', icon: <IconMuseum />,
    title: '내 미술관',      sub: 'Art Journal',
    en: '저장된 감상 기록 보기',
    to: '/journal',
  },
]

function CornerBracket({ top, right, bottom, left }) {
  return (
    <div style={{
      position: 'absolute',
      width: 22, height: 22,
      top, right, bottom, left,
      pointerEvents: 'none',
      borderTop:    top    != null ? `1px solid ${BRZ}0.30)` : 'none',
      borderBottom: bottom != null ? `1px solid ${BRZ}0.30)` : 'none',
      borderLeft:   left   != null ? `1px solid ${BRZ}0.30)` : 'none',
      borderRight:  right  != null ? `1px solid ${BRZ}0.30)` : 'none',
    }} />
  )
}

function AiExplainCard() {
  const [open, setOpen] = useState(false)

  const Step = ({ num, title, children }) => (
    <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
      <div style={{
        width: 22, height: 22, borderRadius: '50%', flexShrink: 0, marginTop: 1,
        border: `1px solid ${BRZ}0.35)`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 9, fontWeight: 700, color: `${BRZ2}0.75)`,
      }}>{num}</div>
      <div style={{ flex: 1 }}>
        <p style={{ fontSize: 11, fontWeight: 700, color: 'var(--body)', marginBottom: 5, letterSpacing: 0.3 }}>{title}</p>
        {children}
      </div>
    </div>
  )

  const Code = ({ lines }) => (
    <div style={{ background: 'rgba(0,0,0,0.04)', borderRadius: 3, padding: '8px 10px', marginTop: 6, borderLeft: `2px solid ${BRZ}0.28)` }}>
      {lines.map((l, i) => (
        <p key={i} style={{ fontSize: 9.5, color: 'var(--sub)', fontFamily: 'monospace', lineHeight: 1.8, letterSpacing: 0.2 }}>{l}</p>
      ))}
    </div>
  )

  return (
    <div style={{ border: `1px solid ${BRZ}0.18)`, borderRadius: 3, overflow: 'hidden' }}>
      <button onClick={() => setOpen(o => !o)} style={{
        width: '100%', background: 'transparent', border: 'none', cursor: 'pointer',
        padding: '10px 14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        fontFamily: 'inherit',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 9, color: `${BRZ2}0.45)`, letterSpacing: 2, fontFamily: 'monospace' }}>AI VISION</span>
          <span style={{ fontSize: 9, color: `${BRZ}0.28)` }}>·</span>
          <span style={{ fontSize: 10, color: 'var(--sub)', letterSpacing: 0.5 }}>작품 인식 원리</span>
        </div>
        <span style={{ fontSize: 11, color: `${BRZ}0.38)`, transform: open ? 'rotate(90deg)' : 'none', transition: 'transform 0.2s' }}>›</span>
      </button>

      {open && (
        <div style={{ background: 'rgba(0,0,0,0.02)', padding: '16px 14px', display: 'flex', flexDirection: 'column', gap: 16 }}>

          <Step num="1" title="로컬 CLIP + FAISS — 초고속 화풍 매칭">
            <p style={{ fontSize: 10.5, color: 'var(--sub)', lineHeight: 1.8 }}>
              OpenAI의 <span style={{ color: 'var(--body)', fontWeight: 600 }}>CLIP 모델</span>을 거쳐 이미지를 512차원 벡터로 변환합니다. 구축해 둔 18,455장의 명화 인덱스를 <span style={{ color: 'var(--body)', fontWeight: 600 }}>FAISS</span>로 1ms 안에 초고속 대조하여 가장 닮은 <span style={{ color: 'var(--body)', fontWeight: 600 }}>화가(Artist)의 화풍</span>을 검색합니다.
            </p>
            <Code lines={[
              '별이 빛나는 밤  →  [0.23, -0.87 ...]  →  Vincent van Gogh (유사도 92%)',
              '모네의 수련    →  [0.91,  0.12 ...]  →  Claude Monet (유사도 91%)',
            ]} />
          </Step>

          <div style={{ height: '0.5px', background: `${BRZ}0.12)` }} />

          <Step num="2" title="Gemini Vision + Google Web — 작품명 및 교차 검증">
            <p style={{ fontSize: 10.5, color: 'var(--sub)', lineHeight: 1.8 }}>
              시각 모델(Gemini)로 그림의 디테일을 읽어 구체적인 <span style={{ color: 'var(--body)', fontWeight: 600 }}>작품명(Title)</span>을 파악합니다. 여기에 구글 웹 이미지 검색(Web Detection)을 결합하여 AI의 오인식(환각)을 방지합니다.
            </p>
            <Code lines={[
              'Gemini Vision  →  "Starry Night" (작품명 식별)',
              'Google Web     →  Wikipedia, MoMA 소장처 등 신뢰 도메인 교차 확증',
            ]} />
          </Step>

          <div style={{ height: '0.5px', background: `${BRZ}0.12)` }} />

          <Step num="3" title="하이브리드 다각 검증 — 완벽한 매칭 확정">
            <p style={{ fontSize: 10.5, color: 'var(--sub)', lineHeight: 1.8 }}>
              로컬에서 찾은 화풍 데이터와 외부 AI/웹에서 검증된 작품명이 완벽히 일치할 때, <span style={{ color: 'var(--body)', fontWeight: 600 }}>'완벽 확정(Confirmed)'</span> 상태로 도출하고 풍부한 감정 분석 및 품격 있는 명화 도슨트를 시작합니다.
            </p>
          </Step>

          <div style={{ height: '0.5px', background: `${BRZ}0.12)` }} />

          <Step num="→" title="실제 작품 인식 흐름">
            <Code lines={[
              '사용자 업로드  →  CLIP/FAISS 18,455장 벡터 대조  →  화가(고흐) 도출',
              '                  ↓',
              '   Gemini Vision + Google Web 교차 검색  →  작품명(별이 빛나는 밤) 식별',
              '                  ↓',
              '   [하이브리드 다각 검증]  →  일치 시 \'Confirmed(완벽 확정)\'',
              '                  ↓',
              '   풍부한 감정 분석 및 깊이 있는 맞춤 해설 생성',
            ]} />
          </Step>

          <p style={{ fontSize: 9, color: `${BRZ}0.35)`, textAlign: 'center', letterSpacing: 0.5, lineHeight: 1.7 }}>
            18,455장의 화풍 지문과 멀티모달 AI의 유기적인 하이브리드 교차 검증 시스템
          </p>
        </div>
      )}
    </div>
  )
}

export default function Home() {
  const nav  = useNavigate()
  const { user, logout, deleteAccount } = useAuth()
  const [showDel, setShowDel] = useState(false)

  return (
    <div className="screen" style={{ position: 'relative', background: 'var(--bg)' }}>
      <CornerBracket top={14}    left={14}  />
      <CornerBracket top={14}    right={14} />
      <CornerBracket bottom={14} left={14}  />
      <CornerBracket bottom={14} right={14} />

      <div style={{ padding: '52px 28px 36px', display: 'flex', flexDirection: 'column', flex: 1 }}>

        {/* Header label */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 26 }}>
          <div style={{ flex: 1, height: '0.5px', background: `${BRZ}0.28)` }} />
          <span style={{ fontSize: 8, color: `${BRZ2}0.65)`, letterSpacing: 3, fontWeight: 700 }}>ART · EMOTION · REFLECTION</span>
          <div style={{ flex: 1, height: '0.5px', background: `${BRZ}0.28)` }} />
        </div>

        {/* Main title */}
        <div style={{ textAlign: 'center', marginBottom: 26 }}>
          <h1 style={{
            fontFamily: "'Cinzel', serif",
            fontSize: 34, fontWeight: 600,
            color: 'var(--text)', letterSpacing: 3,
            lineHeight: 1.3, marginBottom: 10,
          }}>Inner Gallery</h1>
          <p style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontSize: 14, color: 'var(--sub)',
            fontStyle: 'italic', letterSpacing: 2, opacity: 0.85,
          }}>마음미술관</p>
        </div>

        <GoldDivider triple />

        {/* Description */}
        <p style={{
          textAlign: 'center',
          fontFamily: "'Noto Serif KR', serif",
          fontSize: 12.5, color: 'var(--sub)',
          lineHeight: 2.1, margin: '22px 4px 30px',
          letterSpacing: 0.3,
        }}>
          명화를 촬영하거나 업로드하면<br />
          색채와 구도를 읽어 감상 여정을 시작합니다
        </p>

        {/* Menu */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {MENU.map(({ num, icon, title, sub, en, to }) => (
            <div
              key={to}
              onClick={() => nav(to)}
              style={{
                display: 'flex', alignItems: 'center', gap: 16,
                padding: '16px 16px',
                border: '1px solid var(--line)',
                borderRadius: 3,
                background: 'rgba(0,0,0,0.025)',
                cursor: 'pointer',
                transition: 'background 0.18s, border-color 0.18s',
                position: 'relative',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.background = `rgba(120,90,50,0.06)`
                e.currentTarget.style.borderColor = `${BRZ2}0.40)`
                e.currentTarget.querySelector('.menu-arrow').style.color = `${BRZ2}0.80)`
                e.currentTarget.querySelector('.menu-arrow').style.transform = 'translateX(3px)'
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = 'rgba(0,0,0,0.025)'
                e.currentTarget.style.borderColor = 'var(--line)'
                e.currentTarget.querySelector('.menu-arrow').style.color = `${BRZ}0.35)`
                e.currentTarget.querySelector('.menu-arrow').style.transform = 'translateX(0)'
              }}
            >
              {/* Icon + Number */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3, flexShrink: 0, width: 28 }}>
                <span style={{ color: `${BRZ2}0.50)`, lineHeight: 1, display: 'flex' }}>{icon}</span>
                <span style={{ fontSize: 8, fontWeight: 400, color: `${BRZ}0.38)`, letterSpacing: 1, fontFamily: 'monospace' }}>{num}</span>
              </div>

              {/* Text */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  fontWeight: 700, fontSize: 15,
                  color: 'var(--text)', letterSpacing: 0.3,
                  marginBottom: 5,
                  fontFamily: "'Noto Serif KR', serif",
                }}>{title}</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                  <span style={{ fontSize: 9, color: 'var(--gold3)', fontStyle: 'italic', letterSpacing: 1.5 }}>{sub}</span>
                  <span style={{ fontSize: 9, color: `${BRZ}0.30)` }}>·</span>
                  <span style={{ fontSize: 10, color: 'var(--sub)', letterSpacing: 0.2 }}>{en}</span>
                </div>
              </div>

              {/* Arrow */}
              <span className="menu-arrow" style={{
                color: `${BRZ}0.35)`, fontSize: 18,
                transition: 'color 0.18s, transform 0.18s',
                flexShrink: 0,
              }}>›</span>
            </div>
          ))}
        </div>

        <div style={{ flex: 1 }} />

        {/* AI 설명 카드 */}
        <div style={{ marginTop: 32, marginBottom: 16 }}>
          <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, var(--line), transparent)', marginBottom: 20 }} />
          <AiExplainCard />
        </div>

        {/* Footer */}
        <div style={{ textAlign: 'center', paddingTop: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <div style={{ flex: 1, height: '0.5px', background: `${BRZ}0.20)` }} />
            <div style={{ width: 5, height: 5, background: `${BRZ}0.35)`, transform: 'rotate(45deg)' }} />
            <div style={{ flex: 1, height: '0.5px', background: `${BRZ}0.20)` }} />
          </div>
          {user ? (
            <p style={{ fontSize: 10, color: `${BRZ}0.50)`, marginBottom: 8, letterSpacing: 0.5 }}>
              {user.username}님의 미술관
            </p>
          ) : (
            <button
              onClick={() => nav('/login')}
              style={{
                background: 'transparent', border: `1px solid ${BRZ}0.30)`,
                cursor: 'pointer', fontSize: 9, color: `${BRZ}0.55)`,
                letterSpacing: 2.5, fontFamily: 'inherit',
                padding: '7px 18px', borderRadius: 2, marginBottom: 8,
              }}
            >로그인 / 회원가입</button>
          )}
          {user && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, marginTop: 4 }}>
              <button onClick={logout} style={{ background: 'transparent', border: 'none', cursor: 'pointer', fontSize: 9, color: 'rgba(180,100,130,0.6)', letterSpacing: 2, fontFamily: 'inherit' }}>
                로그아웃
              </button>
              {!showDel
                ? <button onClick={() => setShowDel(true)} style={{ background: 'transparent', border: 'none', fontSize: 9, color: 'rgba(180,100,130,0.35)', cursor: 'pointer', fontFamily: 'inherit', letterSpacing: 1 }}>계정 탈퇴</button>
                : <div style={{ display: 'flex', gap: 8, justifyContent: 'center', alignItems: 'center' }}>
                    <span style={{ fontSize: 9, color: 'var(--sub)' }}>정말 탈퇴하시겠어요?</span>
                    <button onClick={() => deleteAccount().catch(() => {})} style={{ background: 'transparent', border: '1px solid rgba(180,60,60,0.4)', borderRadius: 2, padding: '2px 10px', fontSize: 9, color: 'rgba(180,60,60,0.7)', cursor: 'pointer', fontFamily: 'inherit' }}>탈퇴</button>
                    <button onClick={() => setShowDel(false)} style={{ background: 'transparent', border: 'none', fontSize: 9, color: 'var(--sub)', cursor: 'pointer', fontFamily: 'inherit' }}>취소</button>
                  </div>
              }
            </div>
          )}
          <p style={{ marginTop: 10, fontSize: 8, color: `${BRZ}0.28)`, letterSpacing: 3.5, fontWeight: 700 }}>
            INNER GALLERY · AI Vision
          </p>
        </div>

      </div>
    </div>
  )
}
