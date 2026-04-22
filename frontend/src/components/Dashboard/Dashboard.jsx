import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { topicAPI, progressAPI, agentAPI } from '../../services/api'
import { useAuth } from '../../hooks/useAuth'
import { 
  BookOpen, 
  Brain, 
  TrendingUp, 
  Zap, 
  ArrowRight,
  Sparkles,
  Target,
  Award
} from 'lucide-react'
import ProgressCard from './ProgressCard'
import TopicCard from './TopicCard'
import AgentStatus from './AgentStatus'
import toast from 'react-hot-toast'

const Dashboard = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [topics, setTopics] = useState([])
  const [progressSummary, setProgressSummary] = useState(null)
  const [studyTips, setStudyTips] = useState('')
  const [agentStatus, setAgentStatus] = useState(null)
  const [recommendedTopic, setRecommendedTopic] = useState(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      
      // Parallel API calls
      const [topicsRes, progressRes, tipsRes] = await Promise.all([
        topicAPI.getAll(),
        progressAPI.getProgressSummary(),
        progressAPI.getStudyTips()
      ])

      setTopics(topicsRes.data)
      setProgressSummary(progressRes.data)
      setStudyTips(tipsRes.data.tips)

      // Get next recommended topic
      try {
        const nextTopicRes = await progressAPI.getNextTopic()
        setRecommendedTopic(nextTopicRes.data)
      } catch (err) {
        // No recommendation available
      }

      // Get agent status
      try {
        const agentRes = await agentAPI.getStatus()
        setAgentStatus(agentRes.data)
      } catch (err) {
        console.log('Agent status not available')
      }

    } catch (error) {
      toast.error('Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
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
          <p className="text-slate-600 font-medium">Loading your dashboard...</p>
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
      {/* Welcome Header */}
      <motion.div variants={item} className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary-500 via-primary-600 to-accent-600 p-8 text-white">
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -mr-32 -mt-32"></div>
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/10 rounded-full -ml-24 -mb-24"></div>
        
        <div className="relative z-10">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring' }}
          >
            <Sparkles className="w-12 h-12 mb-4" />
          </motion.div>
          
          <h1 className="text-4xl font-bold mb-2">
            Welcome back, {user?.username}!
          </h1>
          <p className="text-primary-100 text-lg mb-6">
            Your AI-powered learning journey continues
          </p>

          {recommendedTopic && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate(`/learn/${recommendedTopic.id}`)}
              className="bg-white text-primary-600 px-6 py-3 rounded-xl font-semibold shadow-xl hover:shadow-2xl transition-all flex items-center gap-2"
            >
              <Zap className="w-5 h-5" />
              Start Learning: {recommendedTopic.name}
              <ArrowRight className="w-5 h-5" />
            </motion.button>
          )}
        </div>
      </motion.div>

      {/* Progress Overview */}
      <motion.div variants={item}>
        <h2 className="text-2xl font-bold text-slate-800 mb-4 flex items-center gap-2">
          <TrendingUp className="w-7 h-7 text-primary-600" />
          Your Progress
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <ProgressCard
            icon={BookOpen}
            label="Topics Mastered"
            value={progressSummary?.topics_mastered || 0}
            total={topics.length}
            color="blue"
            delay={0}
          />
          
          <ProgressCard
            icon={Brain}
            label="In Progress"
            value={progressSummary?.topics_in_progress || 0}
            total={topics.length}
            color="purple"
            delay={0.1}
          />
          
          <ProgressCard
            icon={Target}
            label="Avg Knowledge"
            value={Math.round((progressSummary?.average_knowledge || 0) * 100)}
            suffix="%"
            color="green"
            delay={0.2}
          />
          
          <ProgressCard
            icon={Award}
            label="Practice Sessions"
            value={progressSummary?.total_practice_count || 0}
            color="orange"
            delay={0.3}
          />
        </div>
      </motion.div>

      {/* Study Tips */}
      {studyTips && (
        <motion.div variants={item} className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-accent-500 to-pink-500 rounded-xl flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-800">
                Personalized Study Tips
              </h3>
              <p className="text-sm text-slate-500">
                AI-generated recommendations for you
              </p>
            </div>
          </div>
          
          <div 
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: studyTips }}
          />
        </motion.div>
      )}

      {/* Topics Grid */}
      <motion.div variants={item}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <BookOpen className="w-7 h-7 text-primary-600" />
            Available Topics
          </h2>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => navigate('/learn')}
            className="text-primary-600 font-semibold flex items-center gap-2 hover:gap-3 transition-all"
          >
            View All
            <ArrowRight className="w-5 h-5" />
          </motion.button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {topics.slice(0, 6).map((topic, index) => (
            <TopicCard 
              key={topic.id} 
              topic={topic} 
              delay={index * 0.1}
            />
          ))}
        </div>
      </motion.div>

      {/* Agent Status */}
      {agentStatus && (
        <motion.div variants={item}>
          <AgentStatus status={agentStatus} />
        </motion.div>
      )}
    </motion.div>
  )
}

export default Dashboard