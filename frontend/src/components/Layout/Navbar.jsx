import React from 'react'
import { Menu } from 'lucide-react'
import { Wordmark } from './Sidebar'

// Mobile-only top bar; on desktop the sidebar is always visible.
const Navbar = ({ onMenuClick }) => (
  <div className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-ink-800 bg-ink-950/90 px-4 backdrop-blur lg:hidden">
    <Wordmark />
    <button onClick={onMenuClick} className="text-fg-muted hover:text-fg" aria-label="Open menu">
      <Menu className="h-5 w-5" />
    </button>
  </div>
)

export default Navbar
