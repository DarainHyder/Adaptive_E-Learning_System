import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Check, RotateCcw, X } from 'lucide-react'
import { ProgressBar, pct } from '../Common/ui'

const verdict = (score) =>
  score >= 90 ? 'Outstanding.' : score >= 70 ? 'Well done.' : score >= 50 ? 'Getting there.' : 'A good place to start.'

const Results = ({ results, onRetake }) => {
  const navigate = useNavigate()
  const answers = Object.values(results.answers)

  return (
    <div className="mx-auto max-w-3xl animate-fade-up">
      <p className="eyebrow">{results.topicName} · results</p>
      <div className="mt-6 flex flex-col gap-8 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="font-serif text-8xl leading-none text-fg">{Math.round(results.score)}<span className="text-gold-400">%</span></p>
          <p className="display mt-4 text-3xl">{verdict(results.score)}</p>
          <p className="mt-2 text-fg-subtle">{results.correct} of {results.total} correct</p>
        </div>
        {results.mastery !== undefined && (
          <div className="w-full max-w-xs">
            <div className="mb-2 flex justify-between text-xs text-fg-subtle"><span>Updated mastery</span><span>{pct(results.mastery)}</span></div>
            <ProgressBar value={results.mastery} />
          </div>
        )}
      </div>

      <div className="mt-10 flex flex-wrap gap-3">
        <button onClick={onRetake} className="btn-primary"><RotateCcw className="h-4 w-4" /> New quiz</button>
        <button onClick={() => navigate(`/learn/${results.topicId}`)} className="btn-secondary">Review the lesson</button>
        <button onClick={() => navigate('/progress')} className="btn-secondary">View progress</button>
      </div>

      <div className="mt-14">
        <p className="eyebrow mb-4">Review</p>
        <div className="overflow-hidden rounded-2xl border border-ink-700/70 bg-ink-900">
          {answers.map((a, i) => (
            <div key={i} className="flex gap-4 border-b border-ink-700/60 px-5 py-4 last:border-0">
              {a.is_correct ? <Check className="mt-0.5 h-4 w-4 flex-shrink-0 text-ok" /> : <X className="mt-0.5 h-4 w-4 flex-shrink-0 text-bad" />}
              <div className="min-w-0">
                <p className="text-sm text-fg">{a.question}</p>
                <p className="mt-1 text-xs text-fg-subtle">
                  You answered {a.user_answer}{!a.is_correct && <> · correct answer {a.correct_answer}</>}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Results
