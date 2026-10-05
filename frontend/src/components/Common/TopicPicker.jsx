import React, { useEffect, useMemo, useState } from 'react'
import { ArrowUpRight, Lock } from 'lucide-react'
import { topicAPI, progressAPI } from '../../services/api'
import { DifficultyTag, PageLoader, ProgressBar, pct } from './ui'

export const TopicCard = ({ topic, state, onSelect, actionLabel = 'Open', style }) => {
  const mastery = state?.knowledge_level || 0
  const locked = state && state.readiness < 1
  return (
    <button onClick={() => onSelect(topic)} style={style}
      className="card card-hover group flex h-full flex-col p-5 text-left animate-fade-up">
      <div className="flex items-start justify-between gap-3">
        <p className="eyebrow">{topic.category}</p>
        <ArrowUpRight className="h-4 w-4 text-fg-subtle transition-all group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-gold-300" />
      </div>
      <h3 className="mt-3 font-serif text-2xl leading-tight text-fg">{topic.name}</h3>
      <p className="mt-2 line-clamp-2 text-sm leading-6 text-fg-subtle">{topic.description}</p>
      <div className="mt-auto pt-6">
        <div className="mb-3 flex items-center justify-between text-xs">
          <DifficultyTag level={topic.difficulty} />
          {locked ? (
            <span className="flex items-center gap-1 text-fg-subtle" title="Prerequisites not yet mastered">
              <Lock className="h-3 w-3" /> Prerequisites first
            </span>
          ) : (
            <span className="text-fg-muted">{state?.practice_count ? `${pct(mastery)} mastery` : actionLabel}</span>
          )}
        </div>
        <ProgressBar value={mastery} tone={state?.practice_count ? 'gold' : 'muted'} />
      </div>
    </button>
  )
}

const TopicPicker = ({ onSelect, actionLabel }) => {
  const [topics, setTopics] = useState(null)
  const [states, setStates] = useState({})
  const [category, setCategory] = useState('All')

  useEffect(() => {
    topicAPI.getAll().then((r) => setTopics(r.data)).catch(() => setTopics([]))
    progressAPI.getKnowledgeStates()
      .then((r) => setStates(Object.fromEntries(r.data.states.map((s) => [s.topic_id, s]))))
      .catch(() => {})
  }, [])

  const categories = useMemo(() => ['All', ...new Set((topics || []).map((t) => t.category))], [topics])
  if (!topics) return <PageLoader />
  const shown = topics.filter((t) => category === 'All' || t.category === category)

  return (
    <div>
      <div className="mb-6 flex flex-wrap gap-2">
        {categories.map((c) => (
          <button key={c} onClick={() => setCategory(c)}
            className={`rounded-full border px-3.5 py-1.5 text-xs transition-colors ${
              c === category ? 'border-gold-500/50 bg-gold-400/10 text-gold-200' : 'border-ink-700 text-fg-muted hover:text-fg'}`}>
            {c}
          </button>
        ))}
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {shown.map((t, i) => (
          <TopicCard key={t.id} topic={t} state={states[t.id]} onSelect={onSelect} actionLabel={actionLabel}
            style={{ animationDelay: `${Math.min(i, 12) * 30}ms` }} />
        ))}
      </div>
    </div>
  )
}

export default TopicPicker
