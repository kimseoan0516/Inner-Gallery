import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import GoldDivider from '../components/GoldDivider.jsx'

const BRZ  = 'rgba(122,92,56,'
const BRZ2 = 'rgba(154,120,80,'

function Field({ label, type = 'text', value, onChange, placeholder, onEnter }) {
  const [focused, setFocused] = useState(false)
  const [visible, setVisible] = useState(false)
  const isPassword = type === 'password'
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 9, color: 'var(--gold)', fontWeight: 700, letterSpacing: 2, marginBottom: 6 }}>{label}</div>
      <div style={{ position: 'relative' }}>
        <input
          type={isPassword ? (visible ? 'text' : 'password') : type}
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          onKeyDown={e => e.key === 'Enter' && onEnter?.()}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          style={{
            width: '100%', height: 46,
            background: 'var(--bg)',
            border: `1px solid ${focused ? 'rgba(184,145,42,0.6)' : 'var(--line)'}`,
            borderRadius: 2, padding: isPassword ? '0 44px 0 14px' : '0 14px',
            fontSize: 13, color: 'var(--text)',
            fontFamily: 'inherit', outline: 'none',
            transition: 'border-color 0.2s',
            boxSizing: 'border-box',
          }}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setVisible(v => !v)}
            style={{
              position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
              background: 'none', border: 'none', cursor: 'pointer', padding: 4,
              color: 'var(--sub)', opacity: 0.6, display: 'flex', alignItems: 'center',
            }}
          >
            {visible ? (
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
                <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
            ) : (
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            )}
          </button>
        )}
      </div>
    </div>
  )
}

export default function Login() {
  const nav      = useNavigate()
  const location = useLocation()
  const { login, register } = useAuth()
  const [tab,      setTab]      = useState('login')
  const [username, setUsername] = useState('')
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [confirm,  setConfirm]  = useState('')
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState('')
  const [success,  setSuccess]  = useState('')

  const reset = () => { setError(''); setSuccess(''); setUsername(''); setEmail(''); setPassword(''); setConfirm('') }
  const switchTab = (t) => { setTab(t); reset() }

  const submit = async () => {
    setError(''); setSuccess('')
    if (!username.trim()) { setError('이름을 입력해주세요'); return }
    if (!password)        { setError('비밀번호를 입력해주세요'); return }

    setLoading(true)
    try {
      if (tab === 'login') {
        await login({ username: username.trim(), password })
        nav(location.state?.from || '/')
      } else {
        if (!email.trim())      { setError('이메일을 입력해주세요'); setLoading(false); return }
        if (password.length < 6){ setError('비밀번호는 6자 이상이어야 합니다'); setLoading(false); return }
        if (password !== confirm){ setError('비밀번호가 일치하지 않습니다'); setLoading(false); return }
        await register({ username: username.trim(), email: email.trim(), password })
        setSuccess('가입이 완료되었습니다. 로그인해주세요.')
        switchTab('login')
        setUsername(username.trim())
      }
    } catch (e) {
      setError(e.response?.data?.detail || e.message || '오류가 발생했습니다')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="screen" style={{ background: 'var(--bg)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 28px' }}>

      {/* Header — matches Home page */}
      <div style={{ width: '100%', marginBottom: 32 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 24 }}>
          <div style={{ flex: 1, height: '0.5px', background: `${BRZ}0.28)` }} />
          <span style={{ fontSize: 8, color: `${BRZ2}0.65)`, letterSpacing: 3, fontWeight: 700 }}>ART · EMOTION · REFLECTION</span>
          <div style={{ flex: 1, height: '0.5px', background: `${BRZ}0.28)` }} />
        </div>
        <div style={{ textAlign: 'center', marginBottom: 22 }}>
          <h1 style={{
            fontFamily: "'Georgia', 'Noto Serif KR', serif",
            fontSize: 40, fontWeight: 700,
            color: 'var(--text)', letterSpacing: 4,
            lineHeight: 1.2, marginBottom: 10,
          }}>Inner Gallery</h1>
          <p style={{ fontFamily: "'Noto Serif KR', serif", fontSize: 12, color: 'var(--sub)', fontStyle: 'normal', letterSpacing: 8, opacity: 0.75 }}>마 음 　미 술 관</p>
        </div>
        <GoldDivider triple />
      </div>

      {/* Card */}
      <div className="card" style={{ width: '100%', padding: '28px 24px' }}>
        {/* Tabs */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 0, marginBottom: 24, borderBottom: '1px solid var(--line)' }}>
          {[['login','로그인'],['register','회원가입']].map(([key, lbl]) => (
            <button key={key} onClick={() => switchTab(key)} style={{
              background: 'transparent', border: 'none', cursor: 'pointer',
              padding: '10px 0',
              borderBottom: tab === key ? '2px solid var(--gold)' : '2px solid transparent',
              fontSize: 13, fontWeight: tab === key ? 700 : 400,
              color: tab === key ? 'var(--gold2)' : 'var(--sub)',
              fontFamily: 'inherit', letterSpacing: 0.5,
              transition: 'all 0.15s',
              marginBottom: -1,
            }}>{lbl}</button>
          ))}
        </div>

        <Field label="이름" value={username} onChange={setUsername} placeholder="홍길동" onEnter={submit} />
        {tab === 'register' && <Field label="이메일" type="email" value={email} onChange={setEmail} placeholder="example@email.com" onEnter={submit} />}
        <Field label="비밀번호" type="password" value={password} onChange={setPassword} placeholder="6자 이상" onEnter={submit} />
        {tab === 'register' && <Field label="비밀번호 확인" type="password" value={confirm} onChange={setConfirm} placeholder="비밀번호를 다시 입력" onEnter={submit} />}

        {error   && <p style={{ color: '#D47070', fontSize: 12, marginBottom: 12, lineHeight: 1.6 }}>{error}</p>}
        {success && <p style={{ color: 'var(--gold)', fontSize: 12, marginBottom: 12, lineHeight: 1.6 }}>{success}</p>}

        <button className="btn-primary" onClick={submit} disabled={loading}
          style={{ width: '100%', height: 50, fontSize: 13, letterSpacing: 2, marginTop: 4 }}>
          {loading ? '처리 중…' : tab === 'login' ? '로그인' : '가입하기'}
        </button>
      </div>

      <p style={{ marginTop: 20, fontSize: 8, color: `${BRZ}0.28)`, letterSpacing: 3.5, fontWeight: 700, textAlign: 'center' }}>
        INNER GALLERY · AI Vision
      </p>
    </div>
  )
}
