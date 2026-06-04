import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// 마우스 휠로 가로 스크롤 — .hide-scroll 클래스 요소 전체 적용
document.addEventListener('wheel', (e) => {
  const el = e.target.closest('.hide-scroll')
  if (!el) return
  if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) return  // 이미 가로 스크롤 중
  e.preventDefault()
  el.scrollLeft += e.deltaY
}, { passive: false })

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
