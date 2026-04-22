import React from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { BookOpen, Brain, Trophy, ArrowRight } from 'lucide-react'

const TopicCard = ({ topic, delay = 0 }) => {
  const navigate = useNavigate()

  const difficultyColors = {
    beginner: 'bg-green-100 text-green-700 border-green-200',
    intermediate: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    advanced: 'bg-red-100 text-red-700 border-red-200'
  }

  const categoryIcons = {
    'Programming': Brain,
    'AI/ML': Trophy,
    'Web': BookOpen,
    'Database': BookOpen
  }

  const CategoryIcon = categoryIcons[topic.category] || BookOpen

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      whileHover={{ y: -8 }}
      onClick={() => navigate(`/learn/${topic.id}`)}
      className="card cursor-pointer group relative overflow-hidden"
    >
      {/* Background decoration */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-primary-100 to-accent-100 rounded-full -mr-16 -mt-16 opacity-50 group-hover:scale-150 transition-transform duration-500"></div>

      <div className="relative z-10">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
            <CategoryIcon className="w-6 h-6 text-white" />
          </div>

          <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${difficultyColors[topic.difficulty]}`}>
            {topic.difficulty}
          </span>
        </div>

        {/* Content */}
        <h3 className="text-xl font-bold text-slate-800 mb-2 group-hover:text-primary-600 transition-colors">
          {topic.name}
        </h3>

        <p className="text-sm text-slate-600 mb-4 line-clamp-2">
          {topic.description}
        </p>

        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
            {topic.category}
          </span>

          <motion.div
            className="flex items-center gap-2 text-primary-600 font-semibold text-sm"
            whileHover={{ gap: 8 }}
          >
            Start Learning
            <ArrowRight className="w-4 h-4" />
          </motion.div>
        </div>
      </div>
    </motion.div>
  )
}

export default TopicCard