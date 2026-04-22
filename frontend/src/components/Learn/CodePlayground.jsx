import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Play, HelpCircle, CheckCircle, XCircle, Code } from 'lucide-react'
import { learningAPI } from '../../services/api'
import toast from 'react-hot-toast'

const CodePlayground = ({ topicName }) => {
  const [code, setCode] = useState('# Write your Python code here\nprint("Hello, World!")')
  const [output, setOutput] = useState('')
  const [running, setRunning] = useState(false)
  const [error, setError] = useState(false)
  const [hint, setHint] = useState('')
  const [gettingHint, setGettingHint] = useState(false)
  const [attemptCount, setAttemptCount] = useState(0)

  const handleRunCode = async () => {
    setRunning(true)
    setOutput('')
    setError(false)
    setAttemptCount(prev => prev + 1)

    try {
      const response = await learningAPI.checkCode(code)
      
      if (response.data.success) {
        setOutput(response.data.output)
        setError(false)
        if (!response.data.error) {
          toast.success('Code executed successfully!')
        }
      } else {
        setOutput(response.data.output)
        setError(true)
      }
    } catch (err) {
      setOutput('Failed to execute code')
      setError(true)
    } finally {
      setRunning(false)
    }
  }

  const handleGetHint = async () => {
    setGettingHint(true)

    try {
      const response = await learningAPI.askHint({
        question: `I'm trying to practice ${topicName}`,
        challenge: code,
        attempt_count: attemptCount
      })

      setHint(response.data.hint)
    } catch (err) {
      toast.error('Failed to get hint')
    } finally {
      setGettingHint(false)
    }
  }

  const handleClearCode = () => {
    setCode('# Write your Python code here\nprint("Hello, World!")')
    setOutput('')
    setError(false)
    setHint('')
    setAttemptCount(0)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="card"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl flex items-center justify-center">
            <Code className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-800">
              Practice Playground
            </h2>
            <p className="text-sm text-slate-600">
              Try out what you've learned
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleGetHint}
            disabled={gettingHint}
            className="btn-secondary flex items-center gap-2"
          >
            {gettingHint ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
            ) : (
              <HelpCircle className="w-4 h-4" />
            )}
            Get Hint
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleClearCode}
            className="px-4 py-2 rounded-xl border-2 border-slate-200 hover:border-slate-300 font-semibold text-slate-700 transition-all"
          >
            Clear
          </motion.button>
        </div>
      </div>

      {/* Hint Display */}
      <AnimatePresence>
        {hint && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-4 p-4 bg-blue-50 border-l-4 border-blue-500 rounded-lg"
          >
            <div className="flex items-start gap-3">
              <HelpCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-blue-900 mb-1">AI Tutor Hint</h4>
                <p className="text-sm text-blue-800">{hint}</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Code Editor */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Editor */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Code Editor
          </label>
          <div className="relative">
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full h-80 p-4 bg-slate-900 text-green-400 font-mono text-sm rounded-xl border-2 border-slate-700 focus:border-primary-500 focus:ring-4 focus:ring-primary-100 transition-all outline-none resize-none"
              spellCheck="false"
            />
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleRunCode}
            disabled={running}
            className="mt-4 w-full btn-primary flex items-center justify-center gap-2"
          >
            {running ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                Running...
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                Run Code
              </>
            )}
          </motion.button>
        </div>

        {/* Output */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Output
          </label>
          <div className={`h-80 p-4 rounded-xl border-2 overflow-auto ${
            error 
              ? 'bg-red-50 border-red-200' 
              : output 
                ? 'bg-green-50 border-green-200'
                : 'bg-slate-50 border-slate-200'
          }`}>
            {output ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2 mb-3">
                  {error ? (
                    <XCircle className="w-5 h-5 text-red-600" />
                  ) : (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  )}
                  <span className={`font-semibold ${error ? 'text-red-700' : 'text-green-700'}`}>
                    {error ? 'Error' : 'Success'}
                  </span>
                </div>
                <pre className={`font-mono text-sm whitespace-pre-wrap ${
                  error ? 'text-red-800' : 'text-green-800'
                }`}>
                  {output}
                </pre>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400">
                <div className="text-center">
                  <Play className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">Run your code to see output</p>
                </div>
              </div>
            )}
          </div>

          {attemptCount > 0 && (
            <div className="mt-4 text-sm text-slate-600 text-center">
              Attempts: {attemptCount}
            </div>
          )}
        </div>
      </div>

      {/* Tips */}
      <div className="mt-6 p-4 bg-primary-50 rounded-xl border border-primary-100">
        <h4 className="font-semibold text-primary-900 mb-2 flex items-center gap-2">
          <HelpCircle className="w-4 h-4" />
          Playground Tips
        </h4>
        <ul className="text-sm text-primary-800 space-y-1">
          <li>• Try modifying the examples from the lesson</li>
          <li>• Experiment with different inputs and outputs</li>
          <li>• Use the "Get Hint" button if you're stuck</li>
          <li>• Practice makes perfect - don't be afraid to make mistakes!</li>
        </ul>
      </div>
    </motion.div>
  )
}

export default CodePlayground