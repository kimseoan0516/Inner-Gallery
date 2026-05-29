import { useState } from 'react'
import { useAuth } from '../context/AuthContext.jsx'

export default function LoginModal({ onSuccess, onClose }) {
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
  const switchTab = t => { setTab(t); reset() }

  const submit = async () => {
    setError(''); setSuccess('')
    if (!username.trim()) { setError('이름을 입력해주세요'); return }
    if (!password)        { setError('비밀번호를 입력해주세요'); return }
    setLoading(true)
    try {
      if (tab === 'login') {
        await login({ username: username.trim(), password })
        onSuccess()
      } else {
        if (!email.trim())       { setError('이메일을 입력해주세요'); setLoading(false); return }
        if (password.length < 6) { setError('비밀번호는 6자 이상이어야 합니다'); setLoading(false); return }
        if (password !== confirm) { setError('비밀번호가 일치하지 않습니다'); setLoading(false); return }
        await register({ username: username.trim(), email: email.trim(), password })
        setSuccess('가입 완료! 로그인해주세요.')
        switchTab('login')
        setUsername(username.trim())
      }
    } catch (e) {
      setError(e.response?.data?.detail || e.message || '오류가 발생했습니다')
    } finally {
      setLoading(false)
    }
  }

  const FIELDS = [
    { label: '이름',         type: 'text',     value: username, onChange: setUsername, placeholder: '홍길동' },
    ...(tab === 'register' ? [{ label: '이메일', type: 'email', value: email, onChange: setEmail, placeholder: 'example@email.com' }] : []),
    { label: '비밀번호',     type: 'password', value: password, onChange: setPassword, placeholder: '6자 이상' },
    ...(tab === 'register' ? [{ label: '비밀번호 확인', type: 'password', value: confirm, onChange: setConfirm, placeholder: '비밀번호를 다시 입력' }] : []),
  ]

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 9999,
        background: 'rgba(28,20,12,0.65)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '0 24px',
      }}
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <div style={{
        width: '100%', maxWidth: 360,
        background: 'var(--card)',
        borderRadius: 4,
        padding: '28px 24px 20px',
        border: '1px solid var(--line)',
        boxShadow: '0 8px 40px rgba(0,0,0,0.18)',
      }}>
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <p style={{ fontSize: 9, color: 'var(--gold)', letterSpacing: 3, fontWeight: 700, marginBottom: 4 }}>
            감상을 저장하려면 로그인이 필요해요
          </p>
          <div style={{ width: 36, height: '0.5px', background: 'rgba(184,145,42,0.35)', margin: '8px auto 0' }} />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', borderBottom: '1px solid var(--line)', marginBottom: 20 }}>
          {[['login', '로그인'], ['register', '회원가입']].map(([key, lbl]) => (
            <button key={key} onClick={() => switchTab(key)} style={{
              background: 'transparent', border: 'none', cursor: 'pointer',
              padding: '9px 0',
              borderBottom: tab === key ? '2px solid var(--gold)' : '2px solid transparent',
              fontSize: 12, fontWeight: tab === key ? 700 : 400,
              color: tab === key ? 'var(--gold2)' : 'var(--sub)',
              fontFamily: 'inherit', letterSpacing: 0.5,
              transition: 'all 0.15s', marginBottom: -1,
            }}>{lbl}</button>
          ))}
        </div>

        {FIELDS.map(f => (
          <div key={f.label} style={{ marginBottom: 13 }}>
            <div style={{ fontSize: 9, color: 'var(--gold)', fontWeight: 700, letterSpacing: 2, marginBottom: 5 }}>{f.label}</div>
            <input
              type={f.type}
              value={f.value}
              onChange={e => f.onChange(e.target.value)}
              placeholder={f.placeholder}
              onKeyDown={e => e.key === 'Enter' && submit()}
              style={{
                width: '100%', height: 42, background: 'var(--bg)',
                border: '1px solid var(--line)', borderRadius: 2,
                padding: '0 12px', fontSize: 13, color: 'var(--text)',
                fontFamily: 'inherit', outline: 'none', boxSizing: 'border-box',
              }}
            />
          </div>
        ))}

        {error   && <p style={{ color: '#D47070', fontSize: 12, marginBottom: 10, lineHeight: 1.6 }}>{error}</p>}
        {success && <p style={{ color: 'var(--gold)', fontSize: 12, marginBottom: 10, lineHeight: 1.6 }}>{success}</p>}

        <button
          className="btn-primary"
          onClick={submit}
          disabled={loading}
          style={{ width: '100%', height: 46, fontSize: 13, letterSpacing: 2, marginTop: 4 }}
        >
          {loading ? '처리 중…' : tab === 'login' ? '로그인하고 저장하기' : '가입하기'}
        </button>

        <button
          onClick={onClose}
          style={{
            width: '100%', marginTop: 10,
            background: 'transparent', border: 'none', cursor: 'pointer',
            fontSize: 11, color: 'var(--sub)', fontFamily: 'inherit',
            letterSpacing: 1, padding: '6px 0',
          }}
        >닫기</button>
      </div>
    </div>
  )
}
