import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AppProvider }  from './context/AppContext.jsx'
import { AuthProvider, useAuth } from './context/AuthContext.jsx'
import Home          from './pages/Home.jsx'
import Upload        from './pages/Upload.jsx'
import Results       from './pages/Results.jsx'
import Journal       from './pages/Journal.jsx'
import JournalDetail from './pages/JournalDetail.jsx'
import Login         from './pages/Login.jsx'
import Routine       from './pages/Routine.jsx'
import Drawing       from './pages/Drawing.jsx'

// PrivateRoute는 저장된 기록(journal/routine) 등 로그인 필수 페이지에만 사용
function PrivateRoute({ children }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return null
  return user ? children : <Navigate to="/login" state={{ from: location.pathname }} replace />
}

function AppRoutes() {
  return (
    <div className="app-shell">
      <Routes>
        <Route path="/login"          element={<Login />} />
        {/* 로그인 없이도 접근 가능 — 저장 시에만 로그인 모달 표시 */}
        <Route path="/"               element={<Home />} />
        <Route path="/upload"         element={<Upload mode="upload" />} />
        <Route path="/camera"         element={<Upload mode="camera" />} />
        <Route path="/results"        element={<Results />} />
        <Route path="/drawing"        element={<Drawing />} />
        {/* 로그인 필수 페이지 */}
        <Route path="/journal"        element={<PrivateRoute><Journal /></PrivateRoute>} />
        <Route path="/journal/detail" element={<PrivateRoute><JournalDetail /></PrivateRoute>} />
        <Route path="/routine"        element={<PrivateRoute><Routine /></PrivateRoute>} />
        <Route path="*"               element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </AppProvider>
    </AuthProvider>
  )
}
