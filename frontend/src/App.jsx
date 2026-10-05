import React, { Suspense, lazy, useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './context/AuthContext'
import { useAuth } from './hooks/useAuth'
import Navbar from './components/Layout/Navbar'
import Sidebar from './components/Layout/Sidebar'
import { PageLoader } from './components/Common/ui'

// Pages (code-split: each route loads its own chunk)
const Login = lazy(() => import('./components/Auth/Login'))
const Register = lazy(() => import('./components/Auth/Register'))
const Dashboard = lazy(() => import('./components/Dashboard/Dashboard'))
const Learn = lazy(() => import('./components/Learn/Learn'))
const Quiz = lazy(() => import('./components/Quiz/Quiz'))
const Progress = lazy(() => import('./components/Progress/Progress'))

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth()
  if (loading) return <PageLoader />
  return user ? children : <Navigate to="/login" />
}

const Shell = ({ children }) => {
  const [open, setOpen] = useState(false)
  const { pathname } = useLocation()
  return (
    <div className="flex min-h-screen">
      <Sidebar open={open} onClose={() => setOpen(false)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Navbar onMenuClick={() => setOpen(true)} />
        <main key={pathname} className="mx-auto w-full max-w-6xl flex-1 px-5 py-10 sm:px-8 lg:py-14">
          {children}
        </main>
        <footer className="mx-auto w-full max-w-6xl px-5 pb-8 sm:px-8">
          <p className="border-t border-ink-800 pt-6 text-xs text-fg-subtle">
            Adaptive · LangGraph multi-agent tutor · transformer knowledge tracing
          </p>
        </footer>
      </div>
    </div>
  )
}

const protectedPage = (Page) => (
  <ProtectedRoute>
    <Shell>
      <Page />
    </Shell>
  </ProtectedRoute>
)

function App() {
  return (
    <AuthProvider>
      <Router>
        <Toaster
          position="bottom-right"
          toastOptions={{
            duration: 3000,
            style: {
              background: '#16161a',
              color: '#ecebe7',
              border: '1px solid #27272d',
              borderRadius: '12px',
              fontSize: '14px',
              padding: '12px 16px',
            },
            success: { iconTheme: { primary: '#ddb36a', secondary: '#16161a' } },
            error: { iconTheme: { primary: '#e38c84', secondary: '#16161a' } },
          }}
        />
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/" element={protectedPage(Dashboard)} />
            <Route path="/learn" element={protectedPage(Learn)} />
            <Route path="/learn/:topicId" element={protectedPage(Learn)} />
            <Route path="/quiz" element={protectedPage(Quiz)} />
            <Route path="/quiz/:topicId" element={protectedPage(Quiz)} />
            <Route path="/progress" element={protectedPage(Progress)} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </Suspense>
      </Router>
    </AuthProvider>
  )
}

export default App
