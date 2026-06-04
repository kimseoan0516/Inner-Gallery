import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { verifyResetToken, resetPassword } from '../api.js'
import GoldDivider from '../components/GoldDivider.jsx'

export default function ResetPassword() {
  const nav = useNavigate()
  const [params] = useSearchParams()
  const token = params.get('token') || ''

  const [step,     setStep]     = useState('checking') // checking | form | done | invalid
  const [password, setPassword] = useState('')
  const [confirm,  setConfirm]  = useState('')
  const [showPw,   setShowPw]   = useState(false)
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState('')

  useEffect(() => {
    if (!token) { setStep('invalid'); return }
    verifyResetToken(token)
      .then(r => setStep(r.valid ? 'form' : 'invalid'))
      .catch(() => setStep('invalid'))
  }, [token])

  const submit = async () => {
    setError('')
    if (!password)            { setError('새 비밀번호를 입력해주세요'); return }
    if (password.length < 6)  { setError('비밀번호는 6자 이상이어야 합니다'); return }
    if (password !== confirm)  { setError('비밀번호가 일치하지 않습니다'); return }
    setLoading(true)
    try {
      await resetPassword(token, password)
      setStep('done')
    } catch (e) {
      setError(e.response?.data?.detail || '오류가 발생했습니다')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="screen" style={{ background: 'var(--bg)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 28px' }}>
      <div style={{ width: '100%', marginBottom: 32, textAlign: 'center' }}>
        <h1 style={{ fontFamily: "'Georgia', 'Noto Serif KR', serif", fontSize: 36, fontWeight: 700, color: 'var(--text)', letterSpacing: 4, marginBottom: 10 }}>
          Inner Gallery
        </h1>
        <p style={{ fontFamily: "'Noto Serif KR', serif", fontSize: 12, color: 'var(--sub)', letterSpacing: 6, opacity: 0.75 }}>마음미술관</p>
        <div style={{ marginTop: 20 }}><GoldDivider triple /></div>
      </div>

      <div className="card" style={{ width: '100%', padding: '28px 24px' }}>
        {step === 'checking' && (
          <p style={{ textAlign: 'center', color: 'var(--sub)', fontSize: 13, padding: '20px 0' }}>링크 확인 중…</p>
        )}

        {step === 'invalid' && (
          <div style={{ textAlign: 'center', padding: '12px 0' }}>
            <p style={{ fontSize: 15, color: 'var(--text)', fontFamily: "'Noto Serif KR', serif", marginBottom: 8 }}>링크가 유효하지 않아요</p>
            <p style={{ fontSize: 12, color: 'var(--sub)', lineHeight: 1.7, marginBottom: 24 }}>만료되었거나 이미 사용된 링크예요.<br/>다시 비밀번호 찾기를 시도해주세요.</p>
            <button className="btn-primary" onClick={() => nav('/login')} style={{ width: '100%', height: 48 }}>로그인으로 돌아가기</button>
          </div>
        )}

        {step === 'form' && (
          <>
            <p style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)', fontFamily: "'Noto Serif KR', serif", marginBottom: 6 }}>새 비밀번호 설정</p>
            <p style={{ fontSize: 12, color: 'var(--sub)', marginBottom: 22, lineHeight: 1.7 }}>새로 사용할 비밀번호를 입력해주세요.</p>

            {/* 새 비밀번호 */}
            <div style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 9, color: 'var(--gold)', fontWeight: 700, letterSpacing: 2, marginBottom: 6 }}>새 비밀번호</div>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && submit()}
                  placeholder="6자 이상"
                  style={{ width: '100%', height: 46, boxSizing: 'border-box', padding: '0 44px 0 14px', borderRadius: 2, border: '1px solid var(--line)', background: 'var(--bg)', color: 'var(--text)', fontSize: 13, fontFamily: 'inherit', outline: 'none' }}
                />
                <button type="button" onClick={() => setShowPw(v => !v)}
                  style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--sub)', opacity: 0.6, display: 'flex', alignItems: 'center' }}>
                  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    {showPw
                      ? <><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></>
                      : <><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></>
                    }
                  </svg>
                </button>
              </div>
            </div>

            {/* 비밀번호 확인 */}
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 9, color: 'var(--gold)', fontWeight: 700, letterSpacing: 2, marginBottom: 6 }}>비밀번호 확인</div>
              <input
                type="password"
                value={confirm}
                onChange={e => setConfirm(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && submit()}
                placeholder="비밀번호를 다시 입력"
                style={{ width: '100%', height: 46, boxSizing: 'border-box', padding: '0 14px', borderRadius: 2, border: '1px solid var(--line)', background: 'var(--bg)', color: 'var(--text)', fontSize: 13, fontFamily: 'inherit', outline: 'none' }}
              />
            </div>

            {error && <p style={{ color: '#D47070', fontSize: 12, marginBottom: 12, lineHeight: 1.6 }}>{error}</p>}

            <button className="btn-primary" onClick={submit} disabled={loading}
              style={{ width: '100%', height: 50, fontSize: 13, letterSpacing: 1, marginTop: 4 }}>
              {loading ? '변경 중…' : '비밀번호 변경하기'}
            </button>
          </>
        )}

        {step === 'done' && (
          <div style={{ textAlign: 'center', padding: '12px 0' }}>
            <div style={{ width: 52, height: 52, borderRadius: '50%', border: '1px solid rgba(184,145,42,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--gold2)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </div>
            <p style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)', fontFamily: "'Noto Serif KR', serif", marginBottom: 8 }}>비밀번호가 변경됐어요</p>
            <p style={{ fontSize: 12, color: 'var(--sub)', lineHeight: 1.7, marginBottom: 24 }}>새 비밀번호로 로그인해주세요.</p>
            <button className="btn-primary" onClick={() => nav('/login')} style={{ width: '100%', height: 48 }}>로그인하기</button>
          </div>
        )}
      </div>
    </div>
  )
}
