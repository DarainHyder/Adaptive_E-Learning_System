import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { progressAPI, topicAPI } from '../../services/api'
import KnowledgeGraph from './KnowledgeGraph'
import { EmptyState, PageHeader, PageLoader, ProgressBar, SectionTitle, Stat, StatStrip, pct } from '../Common/ui'

const reviewLabel = (t) => {
  if (!t.practice_count) return <span className="text-fg-subtle">Not started</span>
  if (t.due_for_review) return <span className="text-gold-300">Due now</span>
  return <span className="text-fg-subtle">in {Math.max(1, Math.round(t.days_until_review || 0))}d</span>
}

const Progress = () => {
  const navigate = useNavigate()
  const [summary, setSummary] = useState(null)
  const [rows, setRows] = useState([])
  const [model, setModel] = useState('')

  useEffect(() => {
    // Three requests total (v1 made one request per topic)
    Promise.all([progressAPI.getProgressSummary(), topicAPI.getAll(), progressAPI.getKnowledgeStates()])
      .then(([s, t, k]) => {
        setSummary(s.data)
        setModel(k.data.model)
        const byId = Object.fromEntries(k.data.states.map((x) => [x.topic_id, x]))
        setRows(t.data.map((topic) => ({ ...topic, knowledge_level: 0, practice_count: 0, ...(byId[topic.id] || {}) })))
      })
      .catch(() => toast.error('Failed to load progress'))
  }, [])

  if (!summary) return <PageLoader />
  const started = rows.filter((r) => r.practice_count > 0)

  return (
    <div className="space-y-12">
      <PageHeader eyebrow="Progress" title="How your knowledge is growing"
        subtitle={`Mastery is tracked with Bayesian Knowledge Tracing; predictions come from a transformer trained on 7M learner interactions. Model: ${model}.`} />

      <StatStrip>
        <Stat label="Mastered" value={summary.topics_mastered} hint={`of ${summary.topics_total} topics`} />
        <Stat label="In progress" value={summary.topics_in_progress} />
        <Stat label="Avg. mastery" value={pct(summary.average_knowledge)} />
        <Stat label="Due for review" value={summary.review_due} />
      </StatStrip>

      {started.length ? <KnowledgeGraph data={rows} /> : (
        <EmptyState title="No data yet">Answer a few quiz questions and your knowledge map appears here.</EmptyState>
      )}

      <section>
        <SectionTitle>All topics</SectionTitle>
        <div className="overflow-x-auto rounded-2xl border border-ink-700/70 bg-ink-900">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b border-ink-700/70 text-left">
                {['Topic', 'Mastery', 'Predicted success', 'Answered', 'Review'].map((h) => (
                  <th key={h} className="eyebrow px-5 py-3 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((t) => (
                <tr key={t.id} onClick={() => navigate(`/learn/${t.id}`)}
                  className="cursor-pointer border-b border-ink-700/40 transition-colors last:border-0 hover:bg-ink-850">
                  <td className="px-5 py-3.5">
                    <p className="text-fg">{t.name}</p>
                    <p className="text-xs text-fg-subtle">{t.category}</p>
                  </td>
                  <td className="w-48 px-5 py-3.5">
                    <div className="flex items-center gap-3">
                      <div className="flex-1"><ProgressBar value={t.knowledge_level} tone={t.practice_count ? 'gold' : 'muted'} /></div>
                      <span className="w-9 text-right text-xs tabular-nums text-fg-muted">{pct(t.knowledge_level)}</span>
                    </div>
                  </td>
                  <td className="px-5 py-3.5 tabular-nums text-fg-muted">{pct(t.predicted_success?.intermediate)}</td>
                  <td className="px-5 py-3.5 tabular-nums text-fg-muted">{t.practice_count}</td>
                  <td className="px-5 py-3.5 text-xs">{reviewLabel(t)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

export default Progress
