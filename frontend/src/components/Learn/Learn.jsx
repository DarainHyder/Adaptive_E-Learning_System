import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useParams, useNavigate } from 'react-router-dom'
import { topicAPI, learningAPI, progressAPI } from '../../services/api'
import { 
  BookOpen, 
  ArrowLeft, 
  Sparkles, 
  Play,
  ChevronRight,
  Lightbulb
} from 'lucide-react'
import LessonViewer from './LessonViewer'
import CodePlayground from './CodePlayground'
import toast from 'react-hot-toast'

const Learn = () => {
  const { topicId } = useParams()
  const navigate = useNavigate()
  
  const [topics, setTopics] = useState([])
  const [selectedTopic, setSelectedTopic] = useState(null)
  const [lesson, setLesson] = useState(null)
  const [loading, setLoading] = useState(false)
  const [generatingLesson, setGeneratingLesson] = useState(false)

  useEffect(() => {
    loadTopics()
  }, [])

  useEffect(() => {
    if (topicId) {
      loadTopicAndLesson(parseInt(topicId))
    }
  }, [topicId])

  const loadTopics = async () => {
    try {
      const response = await topicAPI.getAll()
      setTopics(response.data)
    } catch (error) {
      toast.error('Failed to load topics')
    }
  }

  const loadTopicAndLesson = async (id) => {
    try {
      setLoading(true)
      const topicResponse = await topicAPI.getById(id)
      setSelectedTopic(topicResponse.data)
    } catch (error) {
      toast.error('Failed to load topic')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateLesson = async () => {
    if (!selectedTopic) return

    setGeneratingLesson(true)
    const loadingToast = toast.loading('AI is generating your personalized lesson...')

    try {
      const response = await learningAPI.generateLesson(selectedTopic.id)
      setLesson(response.data)
      toast.success('Lesson generated successfully!', { id: loadingToast })
    } catch (error) {
      toast.error('Failed to generate lesson', { id: loadingToast })
    } finally {
      setGeneratingLesson(false)
    }
  }

  const handleSelectTopic = (topic) => {
    setSelectedTopic(topic)
    setLesson(null)
    navigate(`/learn/${topic.id}`)
  }

  const handleNextTopic = async () => {
    try {
      const response = await progressAPI.getNextTopic(selectedTopic?.id)
      if (response.data) {
        handleSelectTopic(response.data)
      }
    } catch (error) {
      toast.error('No more recommendations')
    }
  }

  if (!selectedTopic && !topicId) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="space-y-8"
      >
        {/* Header */}
        <div className="card bg-gradient-to-br from-primary-500 to-accent-600 text-white">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center">
              <BookOpen className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-3xl font-bold mb-2">
                Choose a Topic to Learn
              </h1>
              <p className="text-primary-100">
                AI-powered personalized lessons await you
              </p>
            </div>
          </div>
        </div>

        {/* Topics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {topics.map((topic, index) => (
            <motion.div
              key={topic.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ y: -8 }}
              onClick={() => handleSelectTopic(topic)}
              className="card cursor-pointer group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
                  <BookOpen className="w-6 h-6 text-white" />
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  topic.difficulty === 'beginner' ? 'bg-green-100 text-green-700' :
                  topic.difficulty === 'intermediate' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {topic.difficulty}
                </span>
              </div>

              <h3 className="text-xl font-bold text-slate-800 mb-2 group-hover:text-primary-600 transition-colors">
                {topic.name}
              </h3>

              <p className="text-sm text-slate-600 mb-4">
                {topic.description}
              </p>

              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase">
                  {topic.category}
                </span>
                <ChevronRight className="w-5 h-5 text-primary-600 group-hover:translate-x-1 transition-transform" />
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => {
            setSelectedTopic(null)
            setLesson(null)
            navigate('/learn')
          }}
          className="flex items-center gap-2 text-slate-600 hover:text-primary-600 transition-colors font-medium"
        >
          <ArrowLeft className="w-5 h-5" />
          Back to Topics
        </button>

        {lesson && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleNextTopic}
            className="btn-secondary flex items-center gap-2"
          >
            <Lightbulb className="w-5 h-5" />
            Next Recommended Topic
          </motion.button>
        )}
      </div>

      {/* Topic Header */}
      {selectedTopic && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card bg-gradient-to-br from-primary-500 to-accent-600 text-white"
        >
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3 mb-3">
                <div className="w-14 h-14 bg-white/20 rounded-xl flex items-center justify-center">
                  <BookOpen className="w-7 h-7" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold">{selectedTopic.name}</h1>
                  <p className="text-primary-100">{selectedTopic.category}</p>
                </div>
              </div>
              <p className="text-white/90 mb-4">
                {selectedTopic.description}
              </p>
            </div>

            <span className={`px-4 py-2 rounded-xl text-sm font-semibold ${
              selectedTopic.difficulty === 'beginner' ? 'bg-green-500' :
              selectedTopic.difficulty === 'intermediate' ? 'bg-yellow-500' :
              'bg-red-500'
            }`}>
              {selectedTopic.difficulty}
            </span>
          </div>

          {!lesson && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleGenerateLesson}
              disabled={generatingLesson}
              className="mt-6 bg-white text-primary-600 px-6 py-3 rounded-xl font-semibold shadow-xl hover:shadow-2xl transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {generatingLesson ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
                  Generating Personalized Lesson...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  Generate AI Lesson
                  <Play className="w-5 h-5" />
                </>
              )}
            </motion.button>
          )}
        </motion.div>
      )}

      {/* Lesson Content */}
      <AnimatePresence>
        {lesson && (
          <>
            <LessonViewer lesson={lesson} topic={selectedTopic} />
            <CodePlayground topicName={selectedTopic.name} />
          </>
        )}
      </AnimatePresence>
    </div>
  )
}

export default Learn