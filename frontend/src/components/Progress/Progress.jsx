import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { progressAPI, topicAPI } from '../../services/api'
import { 
  TrendingUp, 
  Target, 
  Award, 
  Brain,
  Calendar,
  Activity,
  Zap
} from 'lucide-react'
import KnowledgeGraph from './KnowledgeGraph'
import ProgressTimeline from './ProgressTimeline'
import toast from 'react-hot-toast'

const Progress = () => {
  const [loading, setLoading] = useState(true)
  const [summary, setSummary] = useState(null)
  const [topicProgress, setTopicProgress] = useState([])

  useEffect(() => {
    loadProgressData()
  }, [])

  const loadProgressData = async () => {
    try {
      setLoading(true)
      
      const [summaryRes, topicsRes] = await Promise.all([
        progressAPI.getProgressSummary(),
        topicAPI.getAll()
      ])

      setSummary(summaryRes.data)

      // Get knowledge state for each topic
      const progressPromises = topicsRes.data.map(async (topic) => {
        try {
          const stateRes = await progressAPI.getKnowledgeState(topic.id)
          return {
            ...topic,
            ...stateRes.data
          }
        } catch (err) {
          return {
            ...topic,
            knowledge_level: 0,
            confidence: 0,
            practice_count: 0
          }
        }
      })

      const progressData = await Promise.all(progressPromises)
      setTopicProgress(progressData)

    } catch (error) {
      toast.error('Failed to load progress data')
    } finally {
      setLoading(false)
    }
  }

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  }

  const item = {
    hidden: { y: 20, opacity: 0 },
    show: { y: 0, opacity: 1 }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-primary-600 mx-auto mb-4"></div>
          <p className="text-slate-600 font-medium">Loading your progress...</p>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="space-y-8"
    >
      {/* Header */}
      <motion.div variants={item} className="card bg-gradient-to-br from-primary-500 to-accent-600 text-white">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center">
            <TrendingUp className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold mb-2">
              Your Learning Progress
            </h1>
            <p className="text-primary-100">
              Track your journey and celebrate your achievements
            </p>
          </div>
        </div>
      </motion.div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div variants={item} className="card group hover:shadow-2xl transition-shadow">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
              <Award className="w-7 h-7 text-white" />
            </div>
            <div>
              <div className="text-3xl font-bold text-slate-800">
                {summary?.topics_mastered || 0}
              </div>
              <div className="text-sm text-slate-600 font-medium">
                Topics Mastered
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div variants={item} className="card group hover:shadow-2xl transition-shadow">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
              <Brain className="w-7 h-7 text-white" />
            </div>
            <div>
              <div className="text-3xl font-bold text-slate-800">
                {summary?.topics_in_progress || 0}
              </div>
              <div className="text-sm text-slate-600 font-medium">
                In Progress
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div variants={item} className="card group hover:shadow-2xl transition-shadow">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
              <Target className="w-7 h-7 text-white" />
            </div>
            <div>
              <div className="text-3xl font-bold text-slate-800">
                {Math.round((summary?.average_knowledge || 0) * 100)}%
              </div>
              <div className="text-sm text-slate-600 font-medium">
                Avg Knowledge
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div variants={item} className="card group hover:shadow-2xl transition-shadow">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
              <Zap className="w-7 h-7 text-white" />
            </div>
            <div>
              <div className="text-3xl font-bold text-slate-800">
                {summary?.total_practice_count || 0}
              </div>
              <div className="text-sm text-slate-600 font-medium">
                Practice Sessions
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Knowledge Graph */}
      <motion.div variants={item}>
        <KnowledgeGraph data={topicProgress} />
      </motion.div>

      {/* Weak and Strong Topics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weak Topics */}
        <motion.div variants={item} className="card">
          <h2 className="text-2xl font-bold text-slate-800 mb-4 flex items-center gap-2">
            <Activity className="w-7 h-7 text-red-600" />
            Topics Needing Focus
          </h2>

          {summary?.weak_topics && summary.weak_topics.length > 0 ? (
            <div className="space-y-3">
              {summary.weak_topics.map((topic, index) => (
                <motion.div
                  key={topic.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="p-4 bg-red-50 rounded-xl border border-red-100"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-slate-800">
                      {topic.name}
                    </span>
                    <span className="text-sm font-bold text-red-600">
                      {Math.round(topic.level * 100)}%
                    </span>
                  </div>
                  <div className="w-full bg-red-200 rounded-full h-2 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${topic.level * 100}%` }}
                      transition={{ delay: 0.3 + (index * 0.1), duration: 0.8 }}
                      className="h-full bg-gradient-to-r from-red-500 to-orange-500 rounded-full"
                    />
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">
              <Target className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No weak topics - great job!</p>
            </div>
          )}
        </motion.div>

        {/* Strong Topics */}
        <motion.div variants={item} className="card">
          <h2 className="text-2xl font-bold text-slate-800 mb-4 flex items-center gap-2">
            <Award className="w-7 h-7 text-green-600" />
            Strong Topics
          </h2>

          {summary?.strong_topics && summary.strong_topics.length > 0 ? (
            <div className="space-y-3">
              {summary.strong_topics.map((topic, index) => (
                <motion.div
                  key={topic.id}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="p-4 bg-green-50 rounded-xl border border-green-100"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-slate-800">
                      {topic.name}
                    </span>
                    <span className="text-sm font-bold text-green-600">
                      {Math.round(topic.level * 100)}%
                    </span>
                  </div>
                  <div className="w-full bg-green-200 rounded-full h-2 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${topic.level * 100}%` }}
                      transition={{ delay: 0.3 + (index * 0.1), duration: 0.8 }}
                      className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full"
                    />
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">
              <Brain className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>Start learning to build strong topics</p>
            </div>
          )}
        </motion.div>
      </div>

      {/* Progress Timeline */}
      <motion.div variants={item}>
        <ProgressTimeline topics={topicProgress} />
      </motion.div>
    </motion.div>
  )
}

export default Progress