import React from 'react'
import { NavLink } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  LayoutDashboard, 
  BookOpen, 
  Brain, 
  TrendingUp, 
  Sparkles 
} from 'lucide-react'

const Sidebar = ({ isOpen }) => {
  const navItems = [
    { 
      path: '/', 
      icon: LayoutDashboard, 
      label: 'Dashboard',
      gradient: 'from-blue-500 to-cyan-500'
    },
    { 
      path: '/learn', 
      icon: BookOpen, 
      label: 'Learn',
      gradient: 'from-purple-500 to-pink-500'
    },
    { 
      path: '/quiz', 
      icon: Brain, 
      label: 'Quiz',
      gradient: 'from-green-500 to-emerald-500'
    },
    { 
      path: '/progress', 
      icon: TrendingUp, 
      label: 'Progress',
      gradient: 'from-orange-500 to-red-500'
    },
  ]

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.aside
          initial={{ x: -300 }}
          animate={{ x: 0 }}
          exit={{ x: -300 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          className="fixed lg:sticky top-0 left-0 h-screen w-64 glass-effect border-r border-white/20 z-50 flex flex-col"
        >
          {/* Logo */}
          <div className="p-6 border-b border-white/10">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center shadow-lg">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="font-bold text-lg gradient-text">
                  AdaptiveLearn
                </h2>
                <p className="text-xs text-slate-500">Multi-Agent AI</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
            {navItems.map((item, index) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 group ${
                    isActive
                      ? 'bg-gradient-to-r from-primary-500 to-accent-500 text-white shadow-lg'
                      : 'hover:bg-white/50 text-slate-700'
                  }`
                }
              >
                {({ isActive }) => (
                  <motion.div
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center gap-3 w-full"
                  >
                    <div className={`p-2 rounded-lg ${isActive ? 'bg-white/20' : `bg-gradient-to-br ${item.gradient}`}`}>
                      <item.icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-white'}`} />
                    </div>
                    <span className="font-semibold">{item.label}</span>
                  </motion.div>
                )}
              </NavLink>
            ))}
          </nav>

          {/* AI Agent Status */}
          <div className="p-4 border-t border-white/10">
            <div className="bg-gradient-to-r from-primary-500/10 to-accent-500/10 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-semibold text-slate-700">
                  AI Agents Active
                </span>
              </div>
              <p className="text-xs text-slate-500">
                5 agents monitoring your learning
              </p>
            </div>
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  )
}

export default Sidebar