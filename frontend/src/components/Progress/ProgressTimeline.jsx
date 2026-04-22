import React from 'react'
import { motion } from 'framer-motion'
import { Calendar, CheckCircle, Clock, TrendingUp } from 'lucide-react'

const ProgressTimeline = ({ topics }) => {
  // Filter and sort topics by last practice date
  const timelineData = topics
    .filter(topic => topic.practice_count > 0)
    .sort((a, b) => new Date(b.last_practiced) - new Date(a.last_practiced))
    .slice(0, 10) // Show last 10 activities

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = Math.abs(now - date)
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays} days ago`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
    return `${Math.floor(diffDays / 30)} months ago`
  }

  const getStatusColor = (level) => {
    if (level >= 0.8) return 'from-green-500 to-emerald-500'
    if (level >= 0.6) return 'from-blue-500 to-cyan-500'
    if (level >= 0.4) return 'from-yellow-500 to-orange-500'
    return 'from-red-500 to-pink-500'
  }

  const getStatusIcon = (level) => {
    if (level >= 0.8) return <CheckCircle className="w-5 h-5 text-white" />
    if (level >= 0.6) return <TrendingUp className="w-5 h-5 text-white" />
    return <Clock className="w-5 h-5 text-white" />
  }

  if (timelineData.length === 0) {
    return (
      <div className="card">
        <h2 className="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-2">
          <Calendar className="w-7 h-7 text-primary-600" />
          Recent Activity
        </h2>
        <div className="text-center py-12 text-slate-500">
          <Calendar className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p>No activity yet - start learning to see your timeline</p>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card"
    >
      <h2 className="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-2">
        <Calendar className="w-7 h-7 text-primary-600" />
        Recent Learning Activity
      </h2>

      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gradient-to-b from-primary-500 to-accent-500"></div>

        {/* Timeline items */}
        <div className="space-y-6">
          {timelineData.map((topic, index) => (
            <motion.div
              key={topic.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="relative pl-16"
            >
              {/* Timeline dot */}
              <div className={`absolute left-0 w-12 h-12 rounded-xl bg-gradient-to-br ${getStatusColor(topic.knowledge_level)} flex items-center justify-center shadow-lg`}>
                {getStatusIcon(topic.knowledge_level)}
              </div>

              {/* Content */}
              <div className="card hover-lift cursor-pointer">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-slate-800 mb-1">
                      {topic.name}
                    </h3>
                    <p className="text-sm text-slate-600">
                      {topic.category} • {topic.difficulty}
                    </p>
                  </div>
                  <span className="text-xs font-semibold text-slate-500 whitespace-nowrap ml-4">
                    {formatDate(topic.last_practiced)}
                  </span>
                </div>

                {/* Progress bar */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-600 font-medium">Knowledge Level</span>
                    <span className="font-bold text-slate-800">
                      {Math.round(topic.knowledge_level * 100)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${topic.knowledge_level * 100}%` }}
                      transition={{ delay: 0.3 + (index * 0.1), duration: 0.8 }}
                      className={`h-full bg-gradient-to-r ${getStatusColor(topic.knowledge_level)} rounded-full`}
                    />
                  </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-slate-100">
                  <div>
                    <div className="text-xs text-slate-500 mb-1">Practice Sessions</div>
                    <div className="text-lg font-bold text-slate-800">{topic.practice_count}</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500 mb-1">Confidence</div>
                    <div className="text-lg font-bold text-slate-800">
                      {Math.round(topic.confidence * 100)}%
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  )
}

export default ProgressTimeline