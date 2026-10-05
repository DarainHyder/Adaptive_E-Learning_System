import React, { useEffect, useState } from 'react'
import { Lightbulb, Play, RotateCcw } from 'lucide-react'
import toast from 'react-hot-toast'
import { learningAPI } from '../../services/api'
import { Spinner } from '../Common/ui'

const DEFAULT_CODE = '# Write your Python code here\nprint("Hello, world!")\n'

const CodePlayground = ({ topicName, topicId, seed }) => {
  const [code, setCode] = useState(DEFAULT_CODE)
  const [practice, setPractice] = useState(null)
  const [result, setResult] = useState(null) // { output, error }
  const [running, setRunning] = useState(false)
  const [hint, setHint] = useState(null)
  const [hinting, setHinting] = useState(false)
  const [attempts, setAttempts] = useState(0)

  // Load code sent from the lesson ("Run in playground" / "Start the challenge")
  useEffect(() => {
    if (!seed) return
    setCode(seed.code)
    setPractice(seed.practice || null)
    setResult(null)
    setHint(null)
    setAttempts(0)
  }, [seed])

  const run = async () => {
    setRunning(true)
    setAttempts((a) => a + 1)
    try {
      const r = await learningAPI.checkCode(code)
      setResult({ output: r.data.output, error: !!r.data.error })
    } catch {
      setResult({ output: 'Could not reach the code runner.', error: true })
    } finally {
      setRunning(false)
    }
  }

  const askHint = async () => {
    setHinting(true)
    try {
      const r = await learningAPI.askHint({
        topic_id: topicId,
        question: practice?.prompt || `Practising ${topicName}`,
        challenge: code,
        last_output: result?.output,
        practice_hints: practice?.hints || [],
        attempt_count: Math.max(1, attempts),
      })
      setHint(r.data)
    } catch {
      toast.error('Could not get a hint')
    } finally {
      setHinting(false)
    }
  }

  const onKeyDown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); run() }
    if (e.key === 'Tab') {
      e.preventDefault()
      const { selectionStart: s, selectionEnd: end } = e.target
      setCode(code.slice(0, s) + '    ' + code.slice(end))
      requestAnimationFrame(() => { e.target.selectionStart = e.target.selectionEnd = s + 4 })
    }
  }

  const matches = practice?.expected_output && result && !result.error &&
    result.output.trim() === String(practice.expected_output).trim()

  return (
    <section className="card p-0 overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-ink-700/70 px-5 py-3">
        <div className="flex items-center gap-3">
          <span className="flex gap-1.5">{[0, 1, 2].map((i) => <span key={i} className="h-2.5 w-2.5 rounded-full bg-ink-700" />)}</span>
          <span className="font-mono text-xs text-fg-subtle">main.py</span>
        </div>
        <div className="flex items-center gap-4">
          <button onClick={askHint} disabled={hinting} className="btn-ghost text-xs">
            {hinting ? <Spinner className="h-3 w-3" /> : <Lightbulb className="h-3.5 w-3.5" />} Hint
          </button>
          <button onClick={() => { setCode(practice?.starter_code || DEFAULT_CODE); setResult(null) }} className="btn-ghost text-xs">
            <RotateCcw className="h-3.5 w-3.5" /> Reset
          </button>
          <button onClick={run} disabled={running} className="btn-primary px-4 py-1.5 text-xs">
            {running ? <Spinner className="h-3 w-3" /> : <Play className="h-3.5 w-3.5" />} Run
          </button>
        </div>
      </div>

      {practice && (
        <div className="border-b border-ink-700/70 bg-ink-850 px-5 py-3 text-sm text-fg-muted">
          <span className="text-fg">Challenge</span> · {practice.prompt}
          <span className="ml-2 text-fg-subtle">Expected: <code className="inline-code">{practice.expected_output}</code></span>
        </div>
      )}

      <div className="grid lg:grid-cols-2">
        <textarea value={code} onChange={(e) => setCode(e.target.value)} onKeyDown={onKeyDown} spellCheck="false"
          aria-label="Code editor"
          className="min-h-[300px] resize-y border-ink-700/70 bg-ink-950 p-5 font-mono text-[13px] leading-6 text-fg outline-none lg:border-r" />
        <div className="min-h-[300px] border-t border-ink-700/70 bg-ink-950 p-5 lg:border-t-0">
          <div className="mb-3 flex items-center justify-between">
            <p className="eyebrow">Output</p>
            {result && (
              <span className={`text-xs ${result.error ? 'text-bad' : matches ? 'text-ok' : 'text-fg-subtle'}`}>
                {result.error ? 'Error' : matches ? 'Matches expected output' : practice ? 'Ran — output differs' : 'Ran successfully'}
              </span>
            )}
          </div>
          {result ? (
            <pre className={`whitespace-pre-wrap font-mono text-[13px] leading-6 ${result.error ? 'text-bad' : 'text-fg-muted'}`}>{result.output}</pre>
          ) : (
            <p className="text-sm text-fg-subtle">Run your code to see output. <span className="font-mono text-xs">Ctrl/⌘ + Enter</span></p>
          )}
        </div>
      </div>

      {hint && (
        <div className="border-t border-ink-700/70 px-5 py-4 text-sm animate-fade-up">
          <p className="eyebrow mb-2 text-gold-400/80">Tutor hint · {hint.hint_level}</p>
          <p className="whitespace-pre-wrap leading-6 text-fg-muted">{hint.hint}</p>
        </div>
      )}
    </section>
  )
}

export default CodePlayground
