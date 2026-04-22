import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useParams, useNavigate } from 'react-router-dom'
import { topicAPI, quizAPI } from '../../services/api'
import { Brain, ArrowLeft, Sparkles, TrendingUp, Award } from 'lucide-react'
import Question from './Question'
import Results from './Results'
import toast from 'react-hot-toast'

const Quiz = () => {
  const { topicId } = useParams()
  const navigate = useNavigate()

  const [topics, setTopics] = useState([])
  const [selectedTopic, setSelectedTopic] = useState(null)
  const [quiz, setQuiz] = useState(null)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState({})
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [generatingQuiz, setGeneratingQuiz] = useState(false)

  useEffect(() => {
    loadTopics()
  }, [])

  useEffect(() => {
    if (topicId) {
      loadTopicAndQuiz(parseInt(topicId))
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

  const loadTopicAndQuiz = async (id) => {
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

  const handleGenerateQuiz = async () => {
    if (!selectedTopic) return

    setGeneratingQuiz(true)
    const loadingToast = toast.loading('AI is generating your adaptive quiz...')

    try {
      const response = await quizAPI.generateQuiz(selectedTopic.id)
      setQuiz(response.data)
      setCurrentQuestionIndex(0)
      setAnswers({})
      setResults(null)
      toast.success('Quiz generated successfully!', { id: loadingToast })
    } catch (error) {
      toast.error('Failed to generate quiz', { id: loadingToast })
    } finally {
      setGeneratingQuiz(false)
    }
  }

  const handleSelectTopic = (topic) => {
    setSelectedTopic(topic)
    setQuiz(null)
    setAnswers({})
    setResults(null)
    navigate(`/quiz/${topic.id}`)
  }

  const handleAnswer = async (questionIndex, selectedAnswer) => {
    const question = quiz.questions[questionIndex]
    
    // Save answer
    setAnswers(prev => ({
      ...prev,
      [questionIndex]: {
        user_answer: selectedAnswer,
        correct_answer: question.correct_answer,
        question: question.question,
        explanation: question.explanation
      }
    }))

    // Submit to backend
    try {
      const response = await quizAPI.submitAnswer({
        topic_id: selectedTopic.id,
        question: question.question,
        user_answer: selectedAnswer,
        correct_answer: question.correct_answer,
        difficulty: quiz.difficulty
      })

      // Update answer with backend response
      setAnswers(prev => ({
        ...prev,
        [questionIndex]: {
          ...prev[questionIndex],
          is_correct: response.data.is_correct,
          explanation: response.data.explanation,
          new_knowledge_level: response.data.new_knowledge_level
        }
      }))
    } catch (error) {
      console.error('Failed to submit answer:', error)
    }
  }

  const handleNext = () => {
    if (currentQuestionIndex < quiz.questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1)
    }
  }

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1)
    }
  }

  const handleSubmitQuiz = () => {
    const answeredCount = Object.keys(answers).length
    const totalQuestions = quiz.questions.length

    if (answeredCount < totalQuestions) {
      toast.error(`Please answer all questions (${answeredCount}/${totalQuestions})`)
      return
    }

    // Calculate results
    const correct = Object.values(answers).filter(a => a.is_correct).length
    const score = (correct / totalQuestions) * 100

    setResults({
      score,
      correct,
      total: totalQuestions,
      answers,
      topicName: selectedTopic.name
    })
  }

  // Topic selection screen
  if (!selectedTopic && !topicId) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="space-y-8"
      >
        <div className="card bg-gradient-to-br from-green-500 to-emerald-600 text-white">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center">
              <Brain className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-3xl font-bold mb-2">
                Test Your Knowledge
              </h1>
              <p className="text-green-100">
                AI-adaptive quizzes that adjust to your level
              </p>
            </div>
          </div>
        </div>

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
                <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
                  <Brain className="w-6 h-6 text-white" />
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  topic.difficulty === 'beginner' ? 'bg-green-100 text-green-700' :
                  topic.difficulty === 'intermediate' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {topic.difficulty}
                </span>
              </div>

              <h3 className="text-xl font-bold text-slate-800 mb-2 group-hover:text-green-600 transition-colors">
                {topic.name}
              </h3>
              <p className="text-sm text-slate-600">
                Test your understanding of {topic.name}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.div>
    )
  }

  // Show results
  if (results) {
    return <Results results={results} onRetake={() => {
      setResults(null)
      setQuiz(null)
      setAnswers({})
    }} />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => {
            setSelectedTopic(null)
            setQuiz(null)
            setAnswers({})
            navigate('/quiz')
          }}
          className="flex items-center gap-2 text-slate-600 hover:text-green-600 transition-colors font-medium"
        >
          <ArrowLeft className="w-5 h-5" />
          Back to Topics
        </button>
      </div>

      {/* Topic Header */}
      {selectedTopic && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card bg-gradient-to-br from-green-500 to-emerald-600 text-white"
        >
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3 mb-3">
                <div className="w-14 h-14 bg-white/20 rounded-xl flex items-center justify-center">
                  <Brain className="w-7 h-7" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold">{selectedTopic.name} Quiz</h1>
                  <p className="text-green-100">Category: {selectedTopic.category}</p>
                </div>
              </div>
            </div>
          </div>

          {!quiz && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleGenerateQuiz}
              disabled={generatingQuiz}
              className="mt-6 bg-white text-green-600 px-6 py-3 rounded-xl font-semibold shadow-xl hover:shadow-2xl transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {generatingQuiz ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-green-600"></div>
                  Generating Adaptive Quiz...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  Generate AI Quiz
                </>
              )}
            </motion.button>
          )}
        </motion.div>
      )}

      {/* Quiz Content */}
      <AnimatePresence mode="wait">
        {quiz && (
          <motion.div
            key="quiz-content"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-6"
          >
            {/* Progress Bar */}
            <div className="card">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-slate-700">
                  Question {currentQuestionIndex + 1} of {quiz.questions.length}
                </span>
                <span className="text-sm font-semibold text-slate-700">
                  Answered: {Object.keys(answers).length}/{quiz.questions.length}
                </span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${((currentQuestionIndex + 1) / quiz.questions.length) * 100}%` }}
                  className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full"
                />
              </div>
            </div>

            {/* Question */}
            <Question
              question={quiz.questions[currentQuestionIndex]}
              questionNumber={currentQuestionIndex + 1}
              selectedAnswer={answers[currentQuestionIndex]?.user_answer}
              onAnswer={(answer) => handleAnswer(currentQuestionIndex, answer)}
              showResult={!!answers[currentQuestionIndex]}
              result={answers[currentQuestionIndex]}
            />

            {/* Navigation */}
            <div className="flex items-center justify-between">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handlePrevious}
                disabled={currentQuestionIndex === 0}
                className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </motion.button>

              {currentQuestionIndex === quiz.questions.length - 1 ? (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleSubmitQuiz}
                  className="btn-primary flex items-center gap-2"
                >
                  <Award className="w-5 h-5" />
                  Submit Quiz
                </motion.button>
              ) : (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleNext}
                  className="btn-primary"
                >
                  Next Question
                </motion.button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default Quiz