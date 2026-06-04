import { useNavigate } from 'react-router-dom'

export default function ResetPassword() {
  const nav = useNavigate()
  // 이메일 직접 입력 방식으로 전환 — 이 페이지는 더 이상 사용하지 않음
  // 로그인 페이지의 "비밀번호 재설정" 모달 사용
  nav('/login', { replace: true })
  return null
}
