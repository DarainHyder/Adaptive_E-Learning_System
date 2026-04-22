import React from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { 
  Award, 
  TrendingUp, 
  RefreshCw, 
  BookOpen, 
  CheckCircle, 
  XCircle,
  Trophy,
  Target
} from 'lucide-react'

const Results = ({ results, onRetake }) => {
  const navigate = useNavigate()
  
  const percentage = results.score
  const isPassed = percentage >= 70

  const getGrade = () => {
    if (percentage >= 90) return { letter: 'A+', color: 'from-green-500 to-emerald-500', message: 'Outstanding!' }
    if (percentage >= 80) return { letter: 'A', color: 'from-green-500 to-emerald-500', message: 'Excellent!' }
    if (percentage >= 70) return { letter: 'B', color: 'from-blue-500 to-cyan-500', message: 'Good Job!' }
    if (percentage >= 60) return { letter: 'C', color: 'from-yellow-500 to-orange-500', message: 'Keep Practicing!' }
    return { letter: 'F', color: 'from-red-500 to-pink-500', message: 'Try Again!' }
  }

  const grade = getGrade()

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="space-y-6"
    >
      {/* Celebration Header */}
      <motion.div
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
        className={`card bg-gradient-to-br ${grade.color} text-white relative overflow-hidden`}
      >
        {/* Background decorations */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -mr-32 -mt-32"></div>
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/10 rounded-full -ml-24 -mb-24"></div>

        <div className="relative z-10">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.4, type: 'spring', stiffness: 200 }}
            className="w-24 h-24 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-4"
          >
            {isPassed ? (
              <Trophy className="w-12 h-12" />
            ) : (
              <Target className="w-12 h-12" />
            )}
          </motion.div>

          <motion.h1
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="text-4xl font-bold text-center mb-2"
          >
            {grade.message}
          </motion.h1>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7 }}
            className="text-center text-white/90 text-lg"
          >
            You scored {results.correct} out of {results.total} questions correctly
          </motion.p>

          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.8, type: 'spring' }}
            className="text-center mt-6"
          >
            <div className="inline-block">
              <div className="text-7xl font-bold">{Math.round(percentage)}%</div>
              <div className="text-2xl font-semibold mt-2">Grade: {grade.letter}</div>
            </div>
          </motion.div>
        </div>
      </motion.div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9 }}
          className="card"
        >
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl flex items-center justify-center">
              <CheckCircle className="w-7 h-7 text-white" />
            </div>
            <div>
              <div className="text-3xl font-bold text-slate-800">{results.correct}</div>
              <div className="text-sm text-slate-600 font-medium">Correct Answers</div>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.0 }}
          className="card"
        >
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-gradient-to-br from-red-500 to-pink-500 rounded-xl flex items-center justify-center">
              <XCircle className="w-7 h-7 text-white" />
            </div>
            <div>
              <div className="text-3xl font-bold text-slate-800">{results.total - results.correct}</div>
              <div className="text-sm text-slate-600 font-medium">Incorrect Answers</div>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.1 }}
          className="card"
        >
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center">
              <Award className="w-7 h-7 text-white" />
            </div>
            <div>
              <div className="text-3xl font-bold text-slate-800">{results.total}</div>
              <div className="text-sm text-slate-600 font-medium">Total Questions</div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Question Review */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.2 }}
        className="card"
      >
        <h2 className="text-2xl font-bold text-slate-800 mb-4 flex items-center gap-2">
          <TrendingUp className="w-7 h-7 text-primary-600" />
          Answer Review
        </h2>

        <div className="space-y-3">
          {Object.entries(results.answers).map(([index, answer], i) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 1.3 + (i * 0.1) }}
              className={`p-4 rounded-xl border-l-4 ${
                answer.is_correct
                  ? 'bg-green-50 border-green-500'
                  : 'bg-red-50 border-red-500'
              }`}
            >
              <div className="flex items-start gap-3">
                {answer.is_correct ? (
                  <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                )}
                <div className="flex-1">
                  <div className="font-semibold text-slate-800 mb-1">
                    Question {parseInt(index) + 1}: {answer.question}
                  </div>
                  <div className="text-sm text-slate-600 space-y-1">
                    <div>
                      <span className="font-medium">Your answer:</span>{' '}
                      <span className={answer.is_correct ? 'text-green-700' : 'text-red-700'}>
                        {answer.user_answer}
                      </span>
                    </div>
                    {!answer.is_correct && (
                      <div>
                        <span className="font-medium">Correct answer:</span>{' '}
                        <span className="text-green-700">{answer.correct_answer}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Action Buttons */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.4 }}
        className="flex flex-wrap gap-4 justify-center"
      >
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onRetake}
          className="btn-secondary flex items-center gap-2"
        >
          <RefreshCw className="w-5 h-5" />
          Retake Quiz
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => navigate(`/learn/${results.topicId}`)}
          className="btn-primary flex items-center gap-2"
        >
          <BookOpen className="w-5 h-5" />
          Review Lesson
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => navigate('/progress')}
          className="btn-primary flex items-center gap-2"
        >
          <TrendingUp className="w-5 h-5" />
          View Progress
        </motion.button>
      </motion.div>

      {/* Motivational Message */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.6 }}
        className="card bg-gradient-to-r from-primary-50 to-accent-50 border-2 border-primary-100"
      >
        <div className="text-center">
          <h3 className="text-xl font-bold gradient-text mb-2">
            {isPassed ? 'Keep Up the Great Work!' : 'Don\'t Give Up!'}
          </h3>
          <p className="text-slate-700">
            {isPassed
              ? 'You\'re making excellent progress. Continue learning to master more topics!'
              : 'Review the lesson and try again. Every attempt helps you learn and improve!'}
          </p>
        </div>
      </motion.div>
    </motion.div>
  )
}

export default Results