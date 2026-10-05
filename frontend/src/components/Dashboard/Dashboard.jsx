import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, RotateCcw } from 'lucide-react'
import toast from 'react-hot-toast'
import { progressAPI, agentAPI } from '../../services/api'
import { useAuth } from '../../hooks/useAuth'
import Markdown from '../Common/Markdown'
import AgentStatus from './AgentStatus'
import { EmptyState, PageHeader, PageLoader, ProgressBar, SectionTitle, Stat, StatStrip, pct } from '../Common/ui'

const greeting = () => {
  const h = new Date().getHours()
  return h < 5 ? 'Good evening' : h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening'
}

const Dashboard = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [summary, setSummary] = useState(null)
  const [recs, setRecs] = useState(null)
  const [review, setReview] = useState([])
  const [tips, setTips] = useState('')
  const [agents, setAgents] = useState(null)

  useEffect(() => {
    progressAPI.getProgressSummary().then((r) => setSummary(r.data)).catch(() => toast.error('Failed to load overview'))
    // Secondary panels load independently and never block the page
    progressAPI.getRecommendations().then((r) => setRecs(r.data)).catch(() => setRecs({ recommendations: [] }))
    progressAPI.getReviewQueue().then((r) => setReview(r.data.due || [])).catch(() => {})
    progressAPI.getStudyTips().then((r) => setTips(r.data.tips)).catch(() => {})
    agentAPI.getStatus().then((r) => setAgents(r.data)).catch(() => {})
  }, [])

  if (!summary) return <PageLoader />
  const next = recs?.next_best

  return (
    <div className="space-y-12">
      <PageHeader
        eyebrow={new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}
        title={<>{greeting()}, <em className="text-gold-300">{user?.username}</em>.</>}
        subtitle={next ? `Your next best step is ${next.name}. ${next.reason}.` : 'Pick a topic to begin. The system calibrates to you as you go.'}
        actions={next && (
          <button onClick={() => navigate(`/learn/${next.topic_id}`)} className="btn-primary">
            Continue with {next.name} <ArrowRight className="h-4 w-4" />
          </button>
        )}
      />

      <StatStrip>
        <Stat label="Mastered" value={`${summary.topics_mastered}`} hint={`of ${summary.topics_total} topics`} />
        <Stat label="In progress" value={summary.topics_in_progress} hint="topics started" />
        <Stat label="Avg. mastery" value={pct(summary.average_knowledge)} hint="across started topics" />
        <Stat label="Answered" value={summary.total_practice_count} hint="questions so far" />
      </StatStrip>

      <div className="grid gap-10 lg:grid-cols-[1.6fr_1fr]">
        <section>
          <SectionTitle action={<Link to="/learn" className="btn-ghost">All topics <ArrowRight className="h-3.5 w-3.5" /></Link>}>
            Recommended for you
          </SectionTitle>
          <div className="overflow-hidden rounded-2xl border border-ink-700/70 bg-ink-900">
            {!recs && <div className="p-6"><PageLoader /></div>}
            {recs?.recommendations?.map((r, i) => (
              <button key={r.topic_id} onClick={() => navigate(`/learn/${r.topic_id}`)}
                className="group flex w-full items-center gap-5 border-b border-ink-700/70 px-5 py-4 text-left transition-colors last:border-0 hover:bg-ink-850">
                <span className="w-6 font-serif text-xl text-fg-subtle group-hover:text-gold-400">{i + 1}</span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-fg">{r.name}</p>
                  <p className="truncate text-xs text-fg-subtle">{r.reason}</p>
                </div>
                <div className="hidden w-28 sm:block">
                  <ProgressBar value={r.current_knowledge} tone={r.current_knowledge > 0 ? 'gold' : 'muted'} />
                  <p className="mt-1.5 text-right text-[11px] text-fg-subtle">{pct(r.current_knowledge)}</p>
                </div>
                <ArrowRight className="h-4 w-4 text-fg-subtle transition-transform group-hover:translate-x-0.5 group-hover:text-gold-300" />
              </button>
            ))}
          </div>
        </section>

        <section className="space-y-10">
          <div>
            <SectionTitle>Due for review</SectionTitle>
            {review.length ? (
              <div className="space-y-2">
                {review.slice(0, 4).map((r) => (
                  <button key={r.topic_id} onClick={() => navigate(`/quiz/${r.topic_id}`)}
                    className="card card-hover flex w-full items-center justify-between p-4 text-left">
                    <div>
                      <p className="text-sm text-fg">{r.name}</p>
                      <p className="text-xs text-fg-subtle">Estimated recall {pct(r.recall)}</p>
                    </div>
                    <RotateCcw className="h-4 w-4 text-gold-400" />
                  </button>
                ))}
              </div>
            ) : (
              <EmptyState title="Nothing due">Your forgetting curve looks healthy.</EmptyState>
            )}
          </div>

          {tips && (
            <div>
              <SectionTitle>Study notes</SectionTitle>
              <div className="card text-sm"><Markdown>{tips}</Markdown></div>
            </div>
          )}
        </section>
      </div>

      {agents && <AgentStatus status={agents} />}
    </div>
  )
}

export default Dashboard
