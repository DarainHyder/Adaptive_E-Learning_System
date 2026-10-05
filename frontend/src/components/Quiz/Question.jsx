import React from 'react'
import { Check, X } from 'lucide-react'
import Markdown from '../Common/Markdown'
import { DifficultyTag, ProgressBar, Spinner, pct } from '../Common/ui'

const LETTERS = ['A', 'B', 'C', 'D']

const Question = ({ question, selectedAnswer, onAnswer, showResult, result, pending }) => {
  const correct = result?.correct_answer

  const styleFor = (opt) => {
    if (!showResult) {
      return selectedAnswer === opt ? 'border-gold-500/60 bg-gold-400/[0.06]' : 'border-ink-700 hover:border-ink-600 hover:bg-ink-850'
    }
    if (opt === correct) return 'border-ok/60 bg-ok/[0.07]'
    if (opt === selectedAnswer) return 'border-bad/60 bg-bad/[0.07]'
    return 'border-ink-700/60 opacity-50'
  }

  return (
    <div className="animate-fade-up">
      <div className="mb-5 flex flex-wrap items-center gap-2">
        {question.difficulty && <DifficultyTag level={question.difficulty} />}
        {question.concept && <span className="chip">{question.concept}</span>}
      </div>
      <div className="display text-3xl leading-snug [&_.markdown]:text-fg [&_.markdown]:leading-snug">
        <Markdown>{question.question}</Markdown>
      </div>

      <div className="mt-8 space-y-3">
        {LETTERS.map((opt) => (
          <button key={opt} onClick={() => !showResult && !pending && onAnswer(opt)} disabled={showResult || pending}
            className={`flex w-full items-center gap-4 rounded-xl border px-4 py-3.5 text-left transition-colors ${styleFor(opt)} ${showResult ? 'cursor-default' : ''}`}>
            <span className={`flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg border font-mono text-xs ${
              showResult && opt === correct ? 'border-ok/60 text-ok'
                : showResult && opt === selectedAnswer ? 'border-bad/60 text-bad'
                  : selectedAnswer === opt ? 'border-gold-500/60 text-gold-300' : 'border-ink-600 text-fg-subtle'}`}>
              {opt}
            </span>
            <span className="flex-1 text-[15px] text-fg">{question.options[opt]}</span>
            {pending && selectedAnswer === opt && <Spinner className="h-4 w-4 text-gold-400" />}
            {showResult && opt === correct && <Check className="h-4 w-4 text-ok" />}
            {showResult && opt === selectedAnswer && opt !== correct && <X className="h-4 w-4 text-bad" />}
          </button>
        ))}
      </div>

      {showResult && (
        <div className="mt-6 rounded-xl border border-ink-700/70 bg-ink-900 p-5 animate-fade-up">
          <p className={`text-sm font-medium ${result.is_correct ? 'text-ok' : 'text-bad'}`}>
            {result.is_correct ? 'Correct' : `Not quite. The answer is ${correct}.`}
          </p>
          {result.explanation && <Markdown className="mt-2 text-sm">{result.explanation}</Markdown>}
          {result.new_knowledge_level !== undefined && (
            <div className="mt-5 flex items-center gap-4">
              <span className="text-xs text-fg-subtle">Mastery</span>
              <div className="flex-1"><ProgressBar value={result.new_knowledge_level} /></div>
              <span className="w-10 text-right text-xs tabular-nums text-fg-muted">{pct(result.new_knowledge_level)}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default Question
