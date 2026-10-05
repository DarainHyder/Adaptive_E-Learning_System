import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { LayoutGrid, BookOpen, CircleDot, LineChart, LogOut, X } from 'lucide-react'
import { useAuth } from '../../hooks/useAuth'

const NAV = [
  { path: '/', icon: LayoutGrid, label: 'Overview', end: true },
  { path: '/learn', icon: BookOpen, label: 'Learn' },
  { path: '/quiz', icon: CircleDot, label: 'Practice' },
  { path: '/progress', icon: LineChart, label: 'Progress' },
]

export const Wordmark = () => (
  <span className="flex items-center gap-2.5">
    <span className="h-2 w-2 rounded-full bg-gold-400 shadow-[0_0_12px_rgba(221,179,106,0.6)]" />
    <span className="font-serif text-2xl tracking-tight text-fg">Adaptive</span>
  </span>
)

const Sidebar = ({ open, onClose }) => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <>
      {open && <div className="fixed inset-0 z-40 bg-black/60 lg:hidden" onClick={onClose} />}
      <aside className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-ink-800 bg-ink-950 px-4 py-6
        transition-transform duration-300 lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="mb-10 flex items-center justify-between px-3">
          <Wordmark />
          <button onClick={onClose} className="text-fg-subtle hover:text-fg lg:hidden" aria-label="Close menu">
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 space-y-1">
          {NAV.map(({ path, icon: Icon, label, end }) => (
            <NavLink key={path} to={path} end={end} onClick={onClose}
              className={({ isActive }) => `group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors ${
                isActive ? 'bg-ink-850 text-fg' : 'text-fg-muted hover:bg-ink-900 hover:text-fg'}`}>
              {({ isActive }) => (
                <>
                  <Icon className={`h-[18px] w-[18px] ${isActive ? 'text-gold-400' : 'text-fg-subtle group-hover:text-fg-muted'}`} strokeWidth={1.75} />
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="mt-6 border-t border-ink-800 pt-5">
          <div className="flex items-center gap-3 px-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full border border-ink-700 bg-ink-850 font-serif text-lg text-gold-300">
              {user?.username?.[0]?.toUpperCase() || '·'}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm text-fg">{user?.username}</p>
              <p className="truncate text-xs capitalize text-fg-subtle">{user?.learning_style || 'mixed'} learner</p>
            </div>
            <button onClick={handleLogout} className="text-fg-subtle transition-colors hover:text-fg" title="Log out" aria-label="Log out">
              <LogOut className="h-4 w-4" strokeWidth={1.75} />
            </button>
          </div>
        </div>
      </aside>
    </>
  )
}

export default Sidebar
