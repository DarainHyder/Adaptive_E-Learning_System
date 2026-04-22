import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { BookOpen, Brain, CheckCircle, ArrowRight, Sparkles } from 'lucide-react'

const LessonViewer = ({ lesson, topic }) => {
  const navigate = useNavigate()
  const [completed, setCompleted] = useState(false)

  // Process HTML content to handle code blocks
  const processContent = (htmlContent) => {
    const parser = new DOMParser()
    const doc = parser.parseFromString(htmlContent, 'text/html')
    
    // Find all code blocks
    const codeBlocks = doc.querySelectorAll('pre code')
    codeBlocks.forEach((block, index) => {
      const code = block.textContent
      const language = block.className.includes('python') ? 'python' : 'javascript'
      block.setAttribute('data-code', code)
      block.setAttribute('data-language', language)
      block.setAttribute('data-index', index)
    })

    return doc.body.innerHTML
  }

  const renderContent = () => {
    const processedContent = processContent(lesson.content)
    
    return (
      <div
        className="lesson-content"
        dangerouslySetInnerHTML={{ __html: processedContent }}
      />
    )
  }

  React.useEffect(() => {
    // After render, replace code blocks with syntax highlighted versions
    const codeBlocks = document.querySelectorAll('[data-code]')
    codeBlocks.forEach((block) => {
      const code = block.getAttribute('data-code')
      const language = block.getAttribute('data-language')
      
      const container = document.createElement('div')
      container.className = 'my-4 rounded-xl overflow-hidden shadow-lg'
      
      const highlightedCode = (
        <SyntaxHighlighter
          language={language}
          style={vscDarkPlus}
          customStyle={{
            margin: 0,
            borderRadius: '0.75rem',
            padding: '1.5rem'
          }}
        >
          {code}
        </SyntaxHighlighter>
      )
      
      block.parentElement.replaceWith(container)
    })
  }, [lesson])

  const handleComplete = () => {
    setCompleted(true)
    setTimeout(() => {
      navigate(`/quiz/${topic.id}`)
    }, 1000)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      {/* Lesson Header */}
      <div className="card bg-gradient-to-r from-primary-50 to-accent-50 border-2 border-primary-100">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold gradient-text">
              AI-Generated Lesson
            </h2>
            <p className="text-sm text-slate-600">
              Personalized for your learning level: {lesson.difficulty}
            </p>
          </div>
        </div>

        {lesson.agent_metadata && (
          <div className="flex flex-wrap gap-2 mt-4">
            <span className="px-3 py-1 bg-white rounded-full text-xs font-semibold text-slate-700 border border-slate-200">
              Teaching Style: {lesson.agent_metadata.teaching_style || 'Adaptive'}
            </span>
            <span className="px-3 py-1 bg-white rounded-full text-xs font-semibold text-slate-700 border border-slate-200">
              Complexity: {lesson.agent_metadata.complexity || lesson.difficulty}
            </span>
            {lesson.agent_metadata.example_count && (
              <span className="px-3 py-1 bg-white rounded-full text-xs font-semibold text-slate-700 border border-slate-200">
                Examples: {lesson.agent_metadata.example_count}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Lesson Content */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="card"
      >
        <style>
          {`
            .lesson-content {
              line-height: 1.8;
            }
            .lesson-content h1 {
              font-size: 2rem;
              font-weight: 800;
              color: #1e293b;
              margin-top: 2rem;
              margin-bottom: 1rem;
              background: linear-gradient(to right, #0ea5e9, #a855f7);
              -webkit-background-clip: text;
              -webkit-text-fill-color: transparent;
            }
            .lesson-content h2 {
              font-size: 1.75rem;
              font-weight: 700;
              color: #334155;
              margin-top: 2rem;
              margin-bottom: 1rem;
              padding-bottom: 0.5rem;
              border-bottom: 2px solid #e0f2fe;
            }
            .lesson-content h3 {
              font-size: 1.35rem;
              font-weight: 600;
              color: #475569;
              margin-top: 1.5rem;
              margin-bottom: 0.75rem;
            }
            .lesson-content p {
              color: #475569;
              margin-bottom: 1rem;
            }
            .lesson-content strong {
              color: #0ea5e9;
              font-weight: 600;
            }
            .lesson-content ul {
              list-style-type: disc;
              margin-left: 1.5rem;
              margin-bottom: 1rem;
              color: #64748b;
            }
            .lesson-content li {
              margin-bottom: 0.5rem;
              padding-left: 0.5rem;
            }
            .lesson-content code:not(pre code) {
              background: #f1f5f9;
              color: #db2777;
              padding: 0.2rem 0.5rem;
              border-radius: 0.375rem;
              font-size: 0.9em;
              font-family: 'Courier New', monospace;
            }
            .lesson-content pre {
              margin: 1.5rem 0;
              border-radius: 0.75rem;
              overflow: hidden;
            }
          `}
        </style>
        
        {renderContent()}
      </motion.div>

      {/* Action Buttons */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="card bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-100"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {completed ? (
              <CheckCircle className="w-8 h-8 text-green-600" />
            ) : (
              <Brain className="w-8 h-8 text-green-600" />
            )}
            <div>
              <h3 className="text-lg font-bold text-slate-800">
                {completed ? 'Lesson Completed!' : 'Ready to Test Your Knowledge?'}
              </h3>
              <p className="text-sm text-slate-600">
                {completed 
                  ? 'Redirecting to quiz...' 
                  : 'Take a quiz to reinforce what you learned'}
              </p>
            </div>
          </div>

          {!completed && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleComplete}
              className="btn-primary flex items-center gap-2"
            >
              Take Quiz
              <ArrowRight className="w-5 h-5" />
            </motion.button>
          )}
        </div>
      </motion.div>

      {/* Knowledge Level Indicator */}
      {lesson.knowledge_level !== undefined && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="card"
        >
          <h3 className="text-lg font-semibold text-slate-800 mb-4">
            Your Knowledge Progress
          </h3>
          <div className="relative">
            <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${lesson.knowledge_level * 100}%` }}
                transition={{ delay: 0.8, duration: 1 }}
                className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full"
              />
            </div>
            <div className="mt-2 text-sm text-slate-600 text-right font-medium">
              {Math.round(lesson.knowledge_level * 100)}% Knowledge Level
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}

export default LessonViewer