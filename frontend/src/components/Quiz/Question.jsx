import React from 'react'
import { motion } from 'framer-motion'
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react'

const Question = ({ question, questionNumber, selectedAnswer, onAnswer, showResult, result }) => {
  const options = ['A', 'B', 'C', 'D']

  const getOptionStyle = (option) => {
    if (!showResult) {
      return selectedAnswer === option
        ? 'border-primary-500 bg-primary-50 ring-4 ring-primary-100'
        : 'border-slate-200 hover:border-primary-300 hover:bg-primary-50'
    }

    // Show results
    if (option === question.correct_answer) {
      return 'border-green-500 bg-green-50 ring-4 ring-green-100'
    }
    
    if (option === selectedAnswer && option !== question.correct_answer) {
      return 'border-red-500 bg-red-50 ring-4 ring-red-100'
    }

    return 'border-slate-200 opacity-50'
  }

  const getOptionIcon = (option) => {
    if (!showResult) return null

    if (option === question.correct_answer) {
      return <CheckCircle className="w-6 h-6 text-green-600" />
    }

    if (option === selectedAnswer && option !== question.correct_answer) {
      return <XCircle className="w-6 h-6 text-red-600" />
    }

    return null
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="card"
    >
      {/* Question Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl flex items-center justify-center text-white font-bold text-lg">
            {questionNumber}
          </div>
          <div className="flex-1">
            <h3 className="text-2xl font-bold text-slate-800">
              {question.question}
            </h3>
            {question.difficulty && (
              <span className={`inline-block mt-2 px-3 py-1 rounded-full text-xs font-semibold ${
                question.difficulty === 'beginner' ? 'bg-green-100 text-green-700' :
                question.difficulty === 'intermediate' ? 'bg-yellow-100 text-yellow-700' :
                'bg-red-100 text-red-700'
              }`}>
                {question.difficulty}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Options */}
      <div className="space-y-3">
        {options.map((option, index) => (
          <motion.button
            key={option}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ scale: showResult ? 1 : 1.02 }}
            whileTap={{ scale: showResult ? 1 : 0.98 }}
            onClick={() => !showResult && onAnswer(option)}
            disabled={showResult}
            className={`w-full p-4 rounded-xl border-2 transition-all text-left flex items-center gap-4 ${getOptionStyle(option)} ${
              showResult ? 'cursor-default' : 'cursor-pointer'
            }`}
          >
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold text-lg flex-shrink-0 ${
              showResult && option === question.correct_answer
                ? 'bg-green-600 text-white'
                : showResult && option === selectedAnswer
                  ? 'bg-red-600 text-white'
                  : selectedAnswer === option
                    ? 'bg-primary-600 text-white'
                    : 'bg-slate-100 text-slate-700'
            }`}>
              {option}
            </div>
            
            <span className="flex-1 font-medium text-slate-800">
              {question.options[option]}
            </span>

            {getOptionIcon(option)}
          </motion.button>
        ))}
      </div>

      {/* Explanation */}
      {showResult && result && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          transition={{ delay: 0.3 }}
          className={`mt-6 p-4 rounded-xl border-l-4 ${
            result.is_correct
              ? 'bg-green-50 border-green-500'
              : 'bg-red-50 border-red-500'
          }`}
        >
          <div className="flex items-start gap-3">
            {result.is_correct ? (
              <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
            )}
            <div className="flex-1">
              <h4 className={`font-bold mb-2 ${
                result.is_correct ? 'text-green-900' : 'text-red-900'
              }`}>
                {result.is_correct ? 'Correct!' : 'Incorrect'}
              </h4>
              <p className={`text-sm ${
                result.is_correct ? 'text-green-800' : 'text-red-800'
              }`}>
                {result.explanation}
              </p>
              
              {result.new_knowledge_level !== undefined && (
                <div className="mt-3 pt-3 border-t border-current/20">
                  <div className="flex items-center justify-between text-xs font-semibold mb-2">
                    <span>Knowledge Level Updated</span>
                    <span>{Math.round(result.new_knowledge_level * 100)}%</span>
                  </div>
                  <div className="w-full bg-white/50 rounded-full h-2 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${result.new_knowledge_level * 100}%` }}
                      transition={{ delay: 0.5, duration: 0.8 }}
                      className={`h-full rounded-full ${
                        result.is_correct
                          ? 'bg-gradient-to-r from-green-500 to-emerald-500'
                          : 'bg-gradient-to-r from-red-500 to-orange-500'
                      }`}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}

export default Question