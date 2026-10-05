import React from 'react'
import { SectionTitle } from '../Common/ui'

const LABELS = {
  knowledge: ['Knowledge', 'Learner model: BKT + transformer KT'],
  teaching: ['Teaching', 'Strategy bandit + lesson writer'],
  assessment: ['Assessment', 'Adaptive quizzes, question bank'],
  tutor: ['Tutor', 'Hints and conversational help'],
  recommendation: ['Recommendation', 'Paths, readiness, review'],
}

const StateDot = ({ state }) => {
  const color = state === 'error' ? 'bg-bad' : state === 'acting' ? 'bg-gold-400 animate-pulse' : state === 'completed' ? 'bg-ok' : 'bg-ink-500'
  return <span className={`inline-block h-1.5 w-1.5 rounded-full ${color}`} />
}

const AgentStatus = ({ status }) => {
  const llm = status.llm || {}
  return (
    <section>
      <SectionTitle action={
        <span className="text-xs text-fg-subtle">
          {status.framework} · LLM {llm.available ? `${llm.provider} ${llm.model || ''}` : 'offline mode'}
        </span>
      }>
        Agent system
      </SectionTitle>
      <div className="overflow-x-auto rounded-2xl border border-ink-700/70 bg-ink-900">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-ink-700/70 text-left">
              {['Agent', 'Role', 'Runs', 'Avg. latency'].map((h) => (
                <th key={h} className="eyebrow px-5 py-3 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Object.entries(LABELS).map(([key, [name, role]]) => {
              const a = status.sub_agents?.[key] || {}
              return (
                <tr key={key} className="border-b border-ink-700/40 last:border-0">
                  <td className="px-5 py-3 text-fg"><span className="flex items-center gap-2.5"><StateDot state={a.state} />{name}</span></td>
                  <td className="px-5 py-3 text-fg-subtle">{role}</td>
                  <td className="px-5 py-3 tabular-nums text-fg-muted">{a.runs ?? 0}</td>
                  <td className="px-5 py-3 tabular-nums text-fg-muted">{a.runs ? `${a.avg_latency_ms} ms` : '—'}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default AgentStatus
